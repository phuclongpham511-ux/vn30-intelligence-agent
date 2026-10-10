"""Classification never propagates upstream authentication material."""
import httpx
import pytest
from ssi_sdk.exceptions import AuthenticationError,APIError,RateLimitError
from src.config.settings import Settings
from src.providers.base import ProviderError,ProviderTransientError
from src.providers.ssi import SsiMarketDataProvider


@pytest.mark.parametrize('error,transient',[
    (httpx.ReadTimeout('SECRET'),True),(RateLimitError('SECRET'),True),
    (APIError('SECRET',status_code=503),True),(APIError('SECRET',status_code=429),True),
    (AuthenticationError('SECRET',status_code=401),False),(APIError('SECRET',status_code=403),False),
    (ValueError('SECRET'),False)])
def test_transient_transport_is_distinct_from_auth_permissions_and_bad_data(error,transient):
    provider=SsiMarketDataProvider(Settings(_env_file=None,ssi_api_key='synthetic-key',ssi_api_secret='synthetic-secret'))
    def fail():raise error
    with pytest.raises(ProviderError) as caught:provider._guard('XYZ','synthetic-test',fail)
    assert isinstance(caught.value,ProviderTransientError)==transient
    assert 'SECRET' not in str(caught.value)
