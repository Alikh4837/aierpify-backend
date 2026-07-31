from typing import Any, Optional

from dynaconf import Dynaconf

from src.exceptions import InternalServerErrorException  # type: ignore[import-untyped]

# Setup Dynaconf
settings = Dynaconf(
    # Load settings from these files
    settings_files=["settings.toml", "secrets.toml"],
    # The Prefix for environment variables, eg `AIERPIFY_FOO=bar`
    envvar_prefix="AIERPIFY",
    # The Key to use in the environment variable to switch environments, eg `export AIERPIFY_APP_ENV=production` or .env file `AIERPIFY_APP_ENV=production`
    env_switcher="AIERPIFY_APP_ENV",
    # Load .env files, the default is True
    load_dotenv=True,
    # Use environments feature, the default is True
    environments=True,
)


def get_setting(
    key: str, default: Optional[Any] = None, raise_error: bool = True
) -> Any:
    """
    Get a setting value from the Dynaconf settings.

    Args:
        key (str): The key of the setting to retrieve.
        default (Optional[Any]): The default value to return if the setting is not found.
        raise_error (bool): Whether to raise an exception when the value is missing.

    Returns:
        Any: The value of the setting or the default value.

    Raises:
        KeyError: If the setting is missing, no default is provided, and raise_error is True.
    """
    value = settings.get(key, default)  # type: ignore

    if raise_error and default is None and value is None:
        raise InternalServerErrorException(
            message=f"Setting '{key}' not found and no default value provided.",
            detail="The requested configuration setting is missing. Please contact the system administrator.",
        )

    return value


# How to use the settings
# from src.config import settings
# print(settings.HOST)
# Refer to https://www.dynaconf.com/#reading-settings-variables for more details
