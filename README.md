# lidl-plus-login

A Python script to get AuthToken for Lidl Plus API given your valid username and password.  
Having this token you may utilize Lidl Plus API and query your receipts, coupons etc.  

## How to use

Required imports are listed in the beginning of the script.  
You may simply run the script if you have dependencies satisfied:  
``python lidl-plus-login.py``

## Result

You will get following JSON result after successful login:
```
data =  {
    "id_token":"xxx..xxx",
    "access_token":"yyy..yyy",
    "expires_in":1200,
    "token_type":"Bearer",
    "refresh_token":"ZZZ..ZZZ",
    "scope":"openid profile lpprofile lpapis offline_access"
}
```

## Acknowledgments

The script was inspired by [LidlApi](https://github.com/KoenZomers/LidlApi) by Koen Zomers and [lidlplus-php-client](https://github.com/bluewalk/lidlplus-php-client)
