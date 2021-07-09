def lambda_handler(event, context):
    print(event)
    response = event["Records"][0]["cf"]["response"];
    headers = response["headers"];
    
    headers['access-control-allow-origin'] = [{"key": 'Access-Control-Allow-Origin', "value": "https://" + event["Records"][0]["cf"]["config"]["distributionDomainName"]}]
    headers['strict-transport-security'] = [{"key": 'Strict-Transport-Security', "value": 'max-age=63072000; includeSubdomains; preload'}]
    headers['content-security-policy'] = [{"key": 'Content-Security-Policy', "value": "default-src 'self'; connect-src 'self' https://sn83xpfcp4.execute-api.us-east-1.amazonaws.com/test; img-src 'self'; script-src 'self'; style-src 'self'; object-src 'none' ; form-action 'self' ; base-uri 'none'; frame-ancestors 'none'"}]
    #headers['content-security-policy'] = [{"key": 'Content-Security-Policy', "value": "default-src 'none'; img-src 'self' data:; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; object-src 'none'"}]
    headers['x-content-type-options'] = [{"key": 'X-Content-Type-Options', "value": 'nosniff'}]
    headers['x-frame-options'] = [{"key": 'X-Frame-Options', "value": 'DENY'}]
    headers['cache-control'] = [{"key": 'Cache-Control', "value": 'no-store'}]
    headers['x-xss-protection'] = [{"key": 'X-XSS-Protection', "value": '1; mode=block'}]
    headers['referrer-policy'] = [{"key": 'Referrer-Policy', "value": 'same-origin'}]
    headers['feature-policy'] = [{"key": 'Feature-Policy', "value": "unsized-media 'none'; geolocation 'self'; camera 'none'; microphone 'none'; picture-in-picture 'none'; autoplay 'none'; display-capture 'none'; layout-animations 'none';  payment 'none'; publickey-credentials-get 'self'; usb 'none'; oversized-images 'none'; midi 'none'; fullscreen 'none'; encrypted-media 'self'; document-domain 'self'"}]
    
    return response
