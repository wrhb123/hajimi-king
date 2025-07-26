import os
import random
from typing import List, Dict, Optional

from dotenv import load_dotenv

from common.Logger import logger

# 只在环境变量不存在时才从.env加载值
load_dotenv(override=False)


class Config:
    GITHUB_TOKENS_STR = os.getenv("GITHUB_TOKENS", "")

    # 获取GitHub tokens列表
    GITHUB_TOKENS = [token.strip() for token in GITHUB_TOKENS_STR.split(',') if token.strip()]
    DATA_PATH = os.getenv('DATA_PATH', 'data')
    PROXY_LIST_STR = os.getenv("PROXY_LIST", "")
    
    # 解析代理列表，支持格式：http://user:pass@host:port,http://host:port,socks5://user:pass@host:port
    PROXY_LIST = []
    if PROXY_LIST_STR:
        for proxy_str in PROXY_LIST_STR.split(','):
            proxy_str = proxy_str.strip()
            if proxy_str:
                PROXY_LIST.append(proxy_str)
    
    # Gemini Balancer配置
    GEMINI_BALANCER_URL = os.getenv("GEMINI_BALANCER_URL", "")
    GEMINI_BALANCER_AUTH = os.getenv("GEMINI_BALANCER_AUTH", "")
    GEMINI_BALANCER_SYNC_ENABLED = os.getenv("GEMINI_BALANCER_SYNC_ENABLED", "false")
    
    # GPT Load Balancer Configuration
    GPT_LOAD_URL = os.getenv('GPT_LOAD_URL', '')
    GPT_LOAD_AUTH = os.getenv('GPT_LOAD_AUTH', '')

    # 文件前缀配置
    VALID_KEY_DETAIL_PREFIX = os.getenv("VALID_KEY_DETAIL_PREFIX", "keys_valid_detail_")
    VALID_KEY_PREFIX = os.getenv("VALID_KEY_PREFIX", "keys_valid_")
    RATE_LIMITED_KEY_PREFIX = os.getenv("RATE_LIMITED_KEY_PREFIX", "gemini_key_429_")
    RATE_LIMITED_KEY_DETAIL_PREFIX = os.getenv("RATE_LIMITED_KEY_DETAIL_PREFIX", "gemini_key_429_detail_")
    
    # 新增：外部应用发送日志文件前缀
    KEYS_SEND_LOG_PREFIX = os.getenv("KEYS_SEND_LOG_PREFIX", "keys_send_")
    KEYS_SEND_DETAIL_PREFIX = os.getenv("KEYS_SEND_DETAIL_PREFIX", "keys_send_detail_")
    
    # 日期范围过滤器配置 (单位：天)
    DATE_RANGE_DAYS = int(os.getenv("DATE_RANGE_DAYS", "730"))  # 默认730天 (约2年)

    # 查询文件路径配置
    QUERIES_FILE = os.getenv("QUERIES_FILE", "queries.txt")

    # 已扫描SHA文件配置
    SCANNED_SHAS_FILE = os.getenv("SCANNED_SHAS_FILE", "scanned_shas.txt")

    # Gemini模型配置
    HAJIMI_CHECK_MODEL = os.getenv("HAJIMI_CHECK_MODEL", "gemini-2.5-flash")

    # 文件路径黑名单配置
    FILE_PATH_BLACKLIST_STR = os.getenv("FILE_PATH_BLACKLIST", "readme,docs,doc/,.md,sample,tutorial")
    FILE_PATH_BLACKLIST = [token.strip().lower() for token in FILE_PATH_BLACKLIST_STR.split(',') if token.strip()]

    @classmethod
    def parse_bool(cls, value: str) -> bool:
        """
        解析布尔值配置，支持多种格式
        
        Args:
            value: 配置值字符串
            
        Returns:
            bool: 解析后的布尔值
        """
        if isinstance(value, bool):
            return value
        
        if isinstance(value, str):
            value = value.strip().lower()
            return value in ('true', '1', 'yes', 'on', 'enabled')
        
        if isinstance(value, int):
            return bool(value)
        
        return False

    @classmethod
    def get_random_proxy(cls) -> Optional[Dict[str, str]]:
        """
        随机获取一个代理配置
        
        Returns:
            Optional[Dict[str, str]]: requests格式的proxies字典，如果未配置则返回None
        """
        if not cls.PROXY_LIST:
            return None
        
        # 随机选择一个代理
        proxy_url = random.choice(cls.PROXY_LIST).strip()
        
        # 返回requests格式的proxies字典
        return {
            'http': proxy_url,
            'https': proxy_url
        }

    @classmethod
    def check(cls) -> bool:
        """
        检查必要的配置是否完整
        
        Returns:
            bool: 配置是否完整
        """
        logger.info("🔍 Checking required configurations...")
        
        errors = []
        
        # 检查GitHub tokens
        if not cls.GITHUB_TOKENS:
            errors.append("GitHub tokens not found. Please set GITHUB_TOKENS environment variable.")
            logger.error("❌ GitHub tokens: Missing")
        else:
            logger.info(f"✅ GitHub tokens: {len(cls.GITHUB_TOKENS)} configured")
        

        
        # 检查数据路径
        if not cls.DATA_PATH:
            errors.append("Data path not configured. Please set DATA_PATH.")
            logger.error("❌ Data path: Missing")
        else:
            logger.info(f"✅ Data path: {cls.DATA_PATH}")
        
        # 检查文件前缀配置
        required_prefixes = [
            (cls.VALID_KEY_DETAIL_PREFIX, "VALID_KEY_DETAIL_PREFIX"),
            (cls.VALID_KEY_PREFIX, "VALID_KEY_LOG_PREFIX"),
            (cls.RATE_LIMITED_KEY_PREFIX, "RATE_LIMITED_KEY_PREFIX"),
            (cls.RATE_LIMITED_KEY_DETAIL_PREFIX, "RATE_LIMITED_KEY_DETAIL_PREFIX")
        ]
        
        for prefix, name in required_prefixes:
            if not prefix:
                errors.append(f"{name} not configured.")
                logger.error(f"❌ {name}: Missing")
            else:
                logger.info(f"✅ {name}: {prefix}")
        
        # 检查Hajimi检验模型配置
        if not cls.HAJIMI_CHECK_MODEL:
            errors.append("HAJIMI_CHECK_MODEL not configured.")
            logger.error("❌ Hajimi check model: Missing")
        else:
            logger.info(f"✅ Hajimi check model: {cls.HAJIMI_CHECK_MODEL}")
        
        # 检查Gemini Balancer配置
        if cls.GEMINI_BALANCER_URL:
            logger.info(f"✅ Gemini Balancer URL: {cls.GEMINI_BALANCER_URL}")
            if not cls.GEMINI_BALANCER_AUTH:
                logger.warning("⚠️ Gemini Balancer Auth: Missing (Balancer功能将被禁用)")
            else:
                logger.info(f"✅ Gemini Balancer Auth: ****")
        else:
            logger.info("ℹ️ Gemini Balancer URL: Not configured (Balancer功能将被禁用)")
        
        if errors:
            logger.error("❌ Configuration check failed:")
            for error in errors:
                logger.error(f"   - {error}")
            logger.info("Please check your .env file and configuration.")
            return False
        
        logger.info("✅ All required configurations are valid")
        return True


logger.info(f"*" * 30 + " CONFIG START " + "*" * 30)
logger.info(f"GITHUB_TOKENS: {len(Config.GITHUB_TOKENS)} tokens")
logger.info(f"DATA_PATH: {Config.DATA_PATH}")
logger.info(f"PROXY_LIST: {len(Config.PROXY_LIST)} proxies configured")
logger.info(f"GEMINI_BALANCER_URL: {Config.GEMINI_BALANCER_URL or 'Not configured'}")
logger.info(f"GEMINI_BALANCER_AUTH: {'Configured' if Config.GEMINI_BALANCER_AUTH else 'Not configured'}")
logger.info(f"GEMINI_BALANCER_SYNC_ENABLED: {Config.parse_bool(Config.GEMINI_BALANCER_SYNC_ENABLED)}")
logger.info(f"GPT_LOAD_URL: {Config.GPT_LOAD_URL or 'Not configured'}")
logger.info(f"GPT_LOAD_AUTH: {'Configured' if Config.GPT_LOAD_AUTH else 'Not configured'}")
logger.info(f"VALID_KEY_PREFIX: {Config.VALID_KEY_PREFIX}")
logger.info(f"RATE_LIMITED_KEY_PREFIX: {Config.RATE_LIMITED_KEY_PREFIX}")
logger.info(f"KEYS_SEND_PREFIX: {Config.KEYS_SEND_PREFIX}")
logger.info(f"VALID_KEY_DETAIL_PREFIX: {Config.VALID_KEY_DETAIL_PREFIX}")
logger.info(f"RATE_LIMITED_KEY_DETAIL_PREFIX: {Config.RATE_LIMITED_KEY_DETAIL_PREFIX}")
logger.info(f"KEYS_SEND_DETAIL_PREFIX: {Config.KEYS_SEND_DETAIL_PREFIX}")
logger.info(f"DATE_RANGE_DAYS: {Config.DATE_RANGE_DAYS} days")
logger.info(f"QUERIES_FILE: {Config.QUERIES_FILE}")
logger.info(f"SCANNED_SHAS_FILE: {Config.SCANNED_SHAS_FILE}")
logger.info(f"HAJIMI_CHECK_MODEL: {Config.HAJIMI_CHECK_MODEL}")
logger.info(f"FILE_PATH_BLACKLIST: {len(Config.FILE_PATH_BLACKLIST)} items")
logger.info(f"*" * 30 + " CONFIG END " + "*" * 30)

# 创建全局配置实例
config = Config()
