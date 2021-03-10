# Apim Test Utils
NHSD helpers for API testing.


## Setup
A wheel is built each time this repository is updated. This will be hosted on [Github](https://github.com/NHSDigital/apim-test-utils/releases).

### Install using pip
You can either download the .whl or point directly to the source.
```bash
# directly from source
$ pip install https://github.com/NHSDigital/apim-test-utils/releases/download/<version>/<file_name>.whl

# downloaded file
$ pip install <file_name>.whl
```

### Install using poetry
If you are using poetry you can add it in your pyprotect.toml file as a dependency:
```toml
[tool.poetry.dependencies]
api-test-utils = {url = "https://github.com/NHSDigital/apim-test-utils/releases/download/<version>/<file_name>.whl"}
```

## Available helpers
* Oauth
* Apigee
* PDS (WIP)


## Get started with the OAuthHelper
The OAuthHelper is a collection of methods to help make it easier for a tester to communicate with identity service 
e.g. requesting an access token or creating a jwt.

### Basic example below:
```python
from api_test_utils.oauth_helper import OauthHelper

# Create an instance
# Each instance is asociated with an app
oauth = OauthHelper("<client_id>", "<client_secret>", "<callback_url>")

# Get a token
token = oauth.get_token_response(grant_type="authorization_code")
```

You can find the full documentation for the OAuthHelper [here](https://nhsd-confluence.digital.nhs.uk/display/APM/Making+use+of+the+OAuth+helper).

## Get starter with ApigeeApis
There are currently two ApigeeApis, these are the ApigeeApiDeveloperApps and the ApigeeApiProducts.

1. ApigeeApiDeveloperApps - allows you to create, modify and delete a developer app on Apigee. This can be particularly 
useful for testing as you can create a test app(s) before the start of a test and then destroy it 
during the clean-up phase after the test has been executed.

2. ApigeeApiProducts - works in conjunction with ApigeeApiDeveloperApps. It allows you to create an Apigee product and grant specific 
   scopes, paths permissions etc. This would then be linked to your test app.
   
### Basic example below:
```python
from api_test_utils.oauth_helper import OauthHelper
from api_test_utils.apigee_api_apps import ApigeeApiDeveloperApps
from api_test_utils.apigee_api_products import ApigeeApiProducts


async def example():
   # Create a new product
   product = ApigeeApiProducts()
   await product.create_new_product()
   
   # Update products allowed paths
   await product.update_paths(paths=["/", "/*"])
   
   # Add scope to product
   product.update_scopes([
      "personal-demographics-service:USER-RESTRICTED", 
      "urn:nhsd:apim:user-nhs-id:aal3:personal-demographics-service"
   ])
   
   # Create a new app
   app = ApigeeApiDeveloperApps()
   await app.create_new_app()
   
   # Assign the new product to the app
   await app.add_api_product([product.name])
   
   # Add a custom attribute to the app
   await app.set_custom_attributes({'asid': '1234567890'})
   
   # Create an OAuthHelper instance with the new app
   oauth = OauthHelper(app.client_id, app.client_secret, app.callback_url)
   
   # Delete the app and the product
   # Note here the app must be destroyed before the product
   await app.destroy_app()
   await product.destroy_product()
```

You can find the full documentation for the Apigee helpers here: [ApigeeApiDeveloperApps](https://nhsd-confluence.digital.nhs.uk/display/APM/Creating+automatic+Apigee+test+applications) 
and here: [ApigeeApiProducts](https://nhsd-confluence.digital.nhs.uk/display/APM/Creating+automatic+Apigee+test+products).
