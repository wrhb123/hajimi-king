import json
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from typing import List

import requests

from common.Logger import logger
from common.config import Config
from utils.file_manager import file_manager


class SyncUtils:
    """同步工具类，负责异步发送keys到外部应用"""

    def __init__(self):
        """初始化同步工具"""
        # Gemini Balancer 配置
        self.balancer_url = Config.GEMINI_BALANCER_URL.rstrip('/') if Config.GEMINI_BALANCER_URL else ""
        self.balancer_auth = Config.GEMINI_BALANCER_AUTH
        self.balancer_sync_enabled = Config.parse_bool(Config.GEMINI_BALANCER_SYNC_ENABLED)
        self.balancer_enabled = bool(self.balancer_url and self.balancer_auth and self.balancer_sync_enabled)

        # GPT Load Balancer 配置
        self.gpt_load_url = Config.GPT_LOAD_URL.rstrip('/') if Config.GPT_LOAD_URL else ""
        self.gpt_load_auth = Config.GPT_LOAD_AUTH
        self.gpt_load_enabled = bool(self.gpt_load_url and self.gpt_load_auth)

        # 创建线程池用于异步执行
        self.executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="SyncUtils")
        self.saving_checkpoint = False

        # 周期性发送控制
        self.batch_interval = 60
        self.batch_timer = None
        self.shutdown_flag = False
        self.file_manager = file_manager

        if not self.balancer_enabled:
            logger.warning("🚫 Gemini Balancer sync disabled - URL or AUTH not configured")
        else:
            logger.info(f"🔗 Gemini Balancer enabled - URL: {self.balancer_url}")

        if not self.gpt_load_enabled:
            logger.warning("🚫 GPT Load Balancer sync disabled - URL or AUTH not configured")
        else:
            logger.info(f"🔗 GPT Load Balancer enabled - URL: {self.gpt_load_url}")

        # 启动周期性发送线程
        self._start_batch_sender()

    def add_keys_to_queue(self, keys: List[str]):
        """
        将keys同时添加到balancer和GPT load的发送队列
        
        Args:
            keys: API keys列表
        """
        if not keys:
            return

        # Acquire lock for checkpoint saving
        while self.saving_checkpoint:
            logger.info(f"📥 Checkpoint is currently being saved, waiting before adding {len(keys)} key(s) to queues...")
            time.sleep(0.5)  # Small delay to prevent busy-waiting

        self.saving_checkpoint = True  # Acquire the lock
        try:
            checkpoint = self.file_manager.load_checkpoint()

            # Gemini Balancer
            if self.balancer_enabled:
                initial_balancer_count = len(checkpoint.wait_send_balancer)
                checkpoint.wait_send_balancer.update(keys)
                new_balancer_count = len(checkpoint.wait_send_balancer)
                added_balancer_count = new_balancer_count - initial_balancer_count
                logger.info(f"📥 Added {added_balancer_count} key(s) to gemini balancer queue (total: {new_balancer_count})")
            else:
                logger.info(f"🚫 Gemini Balancer disabled, skipping {len(keys)} key(s) for gemini balancer queue")

            # GPT Load Balancer
            if self.gpt_load_enabled:
                initial_gpt_count = len(checkpoint.wait_send_gpt_load)
                checkpoint.wait_send_gpt_load.update(keys)
                new_gpt_count = len(checkpoint.wait_send_gpt_load)
                added_gpt_count = new_gpt_count - initial_gpt_count
                logger.info(f"📥 Added {added_gpt_count} key(s) to GPT load balancer queue (total: {new_gpt_count})")
            else:
                logger.info(f"🚫 GPT Load Balancer disabled, skipping {len(keys)} key(s) for GPT load balancer queue")

            self.file_manager.save_checkpoint(checkpoint)
        finally:
            self.saving_checkpoint = False  # Release the lock

    def _send_balancer_worker(self, keys: List[str]) -> str:
        """
        实际执行发送到balancer的工作函数（在后台线程中执行）
        
        Args:
            keys: API keys列表
            
        Returns:
            str: "ok" if success, otherwise an error code string.
        """
        try:
            logger.info(f"🔄 Sending {len(keys)} key(s) to balancer...")

            # 1. 获取当前配置
            config_url = f"{self.balancer_url}/api/config"
            headers = {
                'Cookie': f'auth_token={self.balancer_auth}',
                'User-Agent': 'HajimiKing/1.0'
            }

            logger.info(f"📥 Fetching current config from: {config_url}")

            # 获取当前配置
            response = requests.get(config_url, headers=headers, timeout=30)

            if response.status_code != 200:
                logger.error(f"Failed to get config: HTTP {response.status_code} - {response.text}")
                return "get_config_failed_not_200"

            # 解析配置
            config_data = response.json()

            # 2. 获取当前的API_KEYS数组
            current_api_keys = config_data.get('API_KEYS', [])

            # 3. 合并新keys（去重）
            existing_keys_set = set(current_api_keys)
            new_keys_added = []

            for key in keys:
                if key not in existing_keys_set:
                    current_api_keys.append(key)
                    existing_keys_set.add(key)
                    new_keys_added.append(key)

            if not new_keys_added:
                logger.info(f"ℹ️ All {len(keys)} key(s) already exist in balancer")
                return "ok"

            # 4. 更新配置中的API_KEYS
            config_data['API_KEYS'] = current_api_keys

            logger.info(f"📝 Updating gemini balancer config with {len(new_keys_added)} new key(s)...")

            # 5. 发送更新后的配置到服务器
            update_headers = headers.copy()
            update_headers['Content-Type'] = 'application/json'

            update_response = requests.put(
                config_url,
                headers=update_headers,
                json=config_data,
                timeout=60
            )

            if update_response.status_code != 200:
                logger.error(f"Failed to update config: HTTP {update_response.status_code} - {update_response.text}")
                return "update_config_failed_not_200"

            # 6. 验证是否添加成功
            updated_config = update_response.json()
            updated_api_keys = updated_config.get('API_KEYS', [])
            updated_keys_set = set(updated_api_keys)

            failed_to_add = [key for key in new_keys_added if key not in updated_keys_set]

            if failed_to_add:
                logger.error(f"❌ Failed to add {len(failed_to_add)} key(s): {[key[:10] + '...' for key in failed_to_add]}")
                return "update_failed"

            logger.info(f"✅ All {len(new_keys_added)} new key(s) successfully added to balancer.")
            return "ok"

        except requests.exceptions.Timeout:
            logger.error("❌ Request timeout when connecting to balancer")
            return "timeout"
        except requests.exceptions.ConnectionError:
            logger.error("❌ Connection failed to balancer")
            return "connection_error"
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON response from balancer: {str(e)}")
            return "json_decode_error"
        except Exception as e:
            logger.error(f"❌ Failed to send keys to balancer: {str(e)}", exc_info=True)
            return "exception"

    def _send_gpt_load_worker(self, keys: List[str]) -> str:
        """
        实际执行发送到GPT load balancer的工作函数（在后台线程中执行）
        
        Args:
            keys: API keys列表
            
        Returns:
            str: "ok" if success, otherwise an error code string.
        """
        try:
            # 等待实现
            return "ok"
        except requests.exceptions.Timeout:
            logger.error("❌ Request timeout when connecting to GPT load balancer")
            return "timeout"
        except requests.exceptions.ConnectionError:
            logger.error("❌ Connection failed to GPT load balancer")
            return "connection_error"
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON response from GPT load balancer: {str(e)}")
            return "json_decode_error"
        except Exception as e:
            logger.error(f"❌ Failed to send keys to GPT load balancer: {str(e)}", exc_info=True)
            return "exception"

    def _start_batch_sender(self) -> None:
        """启动批量发送定时器"""
        if self.shutdown_flag:
            return

        # 启动发送任务
        self.executor.submit(self._batch_send_worker)

        # 设置下一次发送定时器
        self.batch_timer = threading.Timer(self.batch_interval, self._start_batch_sender)
        self.batch_timer.daemon = True
        self.batch_timer.start()

    def _batch_send_worker(self) -> None:
        """批量发送worker"""
        while self.saving_checkpoint:
            logger.info(f"📥 Checkpoint is currently being saving, waiting before batch sending...")
            time.sleep(0.5)

        self.saving_checkpoint = True
        try:
            # 加载checkpoint
            checkpoint = self.file_manager.load_checkpoint()

            logger.info(f"📥 Starting batch sending, wait_send_balancer length: {len(checkpoint.wait_send_balancer)}, wait_send_gpt_load length: {len(checkpoint.wait_send_gpt_load)}")
            # 发送gemini balancer队列
            if checkpoint.wait_send_balancer and self.balancer_enabled:
                balancer_keys = list(checkpoint.wait_send_balancer)
                logger.info(f"🔄 Processing {len(balancer_keys)} key(s) from gemini balancer queue")

                result_code = self._send_balancer_worker(balancer_keys)
                if result_code == 'ok':
                    # 清空队列
                    checkpoint.wait_send_balancer.clear()
                    logger.info(f"✅ Gemini balancer queue processed successfully, cleared {len(balancer_keys)} key(s)")
                else:
                    logger.error(f"❌ Gemini balancer queue processing failed with code: {result_code}")
            elif checkpoint.wait_send_balancer and not self.balancer_enabled:
                logger.info(f"🚫 Gemini Balancer disabled, skipping {len(checkpoint.wait_send_balancer)} key(s) in queue")

            # 发送gpt_load队列  
            if checkpoint.wait_send_gpt_load and self.gpt_load_enabled:
                gpt_load_keys = list(checkpoint.wait_send_gpt_load)
                logger.info(f"🔄 Processing {len(gpt_load_keys)} key(s) from GPT load balancer queue")

                result_code = self._send_gpt_load_worker(gpt_load_keys)

                if result_code == 'ok':
                    # 清空队列
                    checkpoint.wait_send_gpt_load.clear()
                    logger.info(f"✅ GPT load balancer queue processed successfully, cleared {len(gpt_load_keys)} key(s)")
                else:
                    logger.error(f"❌ GPT load balancer queue processing failed with code: {result_code}")
            elif checkpoint.wait_send_gpt_load and not self.gpt_load_enabled:
                logger.info(f"🚫 GPT Load Balancer disabled, skipping {len(checkpoint.wait_send_gpt_load)} key(s) in queue")

            # 保存checkpoint
            self.file_manager.save_checkpoint(checkpoint)
        except Exception as e:
            stacktrace = traceback.format_exc()
            logger.error(f"❌ Batch send worker error: {e}\n{stacktrace}")
            logger.error(f"❌ Batch send worker error: {e}")
        finally:
            self.saving_checkpoint = False  # Release the lock

    def shutdown(self) -> None:
        """关闭线程池和定时器"""
        self.shutdown_flag = True

        if self.batch_timer:
            self.batch_timer.cancel()

        self.executor.shutdown(wait=True)
        logger.info("🔚 SyncUtils shutdown complete")


# 创建全局实例
sync_utils = SyncUtils()
