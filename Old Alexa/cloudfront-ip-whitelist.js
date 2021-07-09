
'use strict'; //literal expression, be executed in "strict mode" =>  can not use undeclared variables

exports.handler = (event, context, callback) => {
    const secret = '7l8glehvc15igf3v5noucuept8c2uk327ahpt7v21srgtm20f8d';
    const cloudfrontDomain = 'https://d3gsnj71eleazo.cloudfront.net';
    const domainUrl = '';
    const authDomain = 'https://alexa-app-demo.auth.us-east-1.amazoncognito.com';
    const clientId = '2t6fr8ethjs759ohd11shsckt3';
    const https = require('https');
    const ssoRejectQuerystring = "error_description=Error+in+SAML+Identity+Provider%3B+urn%3Aoasis%3Anames%3Atc%3ASAML%3A2.0%3Astatus%3ARequestDenied%3A+No+SAML+assertion+found+in+the+SAML+response.+&error=access_denied";
    const pingfedEnvironment = 'NAME_FEDERATION';
    const publicList = ["/favicon.ico", "/Logout.html"];
    const externalList = [];




    // create buffer from string
    let binaryData = Buffer.from(clientId +":" + secret, "utf8");
    // decode buffer as base64
    let auth = binaryData.toString("base64");
    var jwt = require('jsonwebtoken'); //Node.js's built-in function to load modules. For a module to access another module's exports or module.exports, it must use require(). => Load jsonwebtoken module.
    var jwkToPem = require('jwk-to-pem');
    var jwk = {}; //jwk verifies jwt
    //const jwkList = [{"alg":"RS256","e":"AQAB","kid":"JlgZXI95POYEurMt7sJ3bsQs1HnqGufGEzNlfjSjCn4=","kty":"RSA","n":"rWHNRUXSUzaNvPmzTsXb9cUXt2RFY7n0auEKqjDfjstJ9iE6K1U90on1-Q3uDDNTGaaLP4jEIoTSqr156jdr4SJuvoXA17gXVoSs7EZp1ZH0bnBb4n5uWcKyAWR4M9mGgBH0IsOlNSUfH_YTCW2RFYTiGmgdoSvxIIMyg8732q3Y41M1ENzSgX_pqnHaDD3xMGLz2SHhlsJjpSpmIl9jiIAG2h1Vn_VRlNUT9qOHjCvgB7kD0JfvefkSRpcmoeyderKcIq6ROsgFHME0BnbldBj-0DM1Qx3uEik2zm0PmbkIz7uNqatw472SjDVLmyXp5miHzfS7iSHrcdNhraEZqQ","use":"sig"},{"alg":"RS256","e":"AQAB","kid":"AruQFmX6b6EeFaGmc0SG6NRb5Ssj9bmv3pwQpa6Bjyk=","kty":"RSA","n":"vPYLu4P7LfRCTllO8a2ziXTrqq-h4FfnwI4p_UlMYPQaQd10YFJzIMqmnbzQaHCkE4-OctplFI_Y8zKjy2ODVZEzxhe6VzNHQUoNKYMsFfI7YgQrNRLz9_tdK9XGqSSpGXMAujySFu4x0hhKuRqIRhvvJNA3fzr5ksCNdeYVoqIHHHJH0Ty_pIJkVq5lo3Z7r1XjsE8o4IKIB2ZOI9jGf9JnjeEQc8yzCc2lQUuUxE7cdFYptLnl2KVu63UsCFp4RVHnZmhySRII7idM3MNtGf-VL90bkPumAwB1ReS0FF3-mnGUZUS8X8F8_mE1g5Fsc_yU13NCMLEN6PIoxyCY7Q","use":"sig"}];
    const jwkList = [{"alg":"RS256","e":"AQAB","kid":"/je8Ux/nelGTAOIyPGIenBmZHPRPRfhs+HZceZiFNdk=","kty":"RSA","n":"qslA33iXRCAbU567_iVPZ7PGSDrDdknzPYUZuv88EXYjpFjzalUVxyRz3cY2J2Hw4k58tm9tifuo30Y9mloRCh3lhw7b6HK41o07tUp3K4GG9n6YsMTzcHv_QneAcO2coJk4Nd9Kqml31Vu6FP5KX36toZCV2hDrXTL8D_Ibq2t3rnE8RU3_ujamRPXve12W4d6AGY1csApL3IsgsPVAd__82dkYn73dtc0thn7ZGdWbLIEmCEq6aBJi0JW0kghLOxHayBvOhfa13uHC8zbJkOdOxRFvRaHqYXjpK-NFGkMDFo8-8CymweF-7H4owGX8kdyCDQ2zCMr7nZfXsZEcBQ","use":"sig"},{"alg":"RS256","e":"AQAB","kid":"sSH8pOcSYeJ+GqNjY2YLy1w2Q+MIlUwfK51MpRq4ifg=","kty":"RSA","n":"32jcbvyf3k3jazob8ZsfM-NQBZ_l636eE3mk8-nvMSJV4g6JognrWNz3z9ARlGf-xhfbfs_zsuKEznRJ3o481dQ8JmE_ZnkqeQa3Xhe4rtwqY5RbIVypDiaHZLxegQ5IYYuD82HsYPpymsMfO7bZFUpavkn3fFr2_6D3AtlOvJSVCr91XzMyfwmj4bjt5cjUczZF11Vjhcyn8RXb49J1AjSui3Z2MEJ-9KZ94dhBtwM_6sPkcO2Zjnvp9wxNr1OzHUBggdVYL81LqOQ7UYRy6TT38cfOyWLgMNlrwecUgxvD_s40Pw6FYYKwQ3CcFZeS4GjEprN3Sr42UYIOcl3X9w","use":"sig"}];

    //Get contents of request
    var request = event.Records[0].cf.request;
    const IP = request.clientIp;
    console.log(request.method + " Request made by " + IP);
    console.log(request.uri);
    console.log(request.querystring);

    function returnError(){
        if (externalList.includes(request.uri)){
           console.log("Rejected page components requested");
            callback(null, request);
        }
        else{
            var response = {
                    status: '302', //temporary redirection
                    statusDescription: 'Found',
                  headers: {
                        location: [{
                            key: 'Location',
                            value: cloudfrontDomain + '/Redirect.html'
                      }]
                   },
               };
            callback(null, response);
        }
    }
    //
    function returnCognitoRedirect(expired){
        var response = {
                status: '302',
                statusDescription: 'Found',
                headers: {
                    location: [{
                        key: 'Location',
                        value: authDomain + '/login?client_id=' + clientId + '&response_type=code&scope=email+openid&redirect_uri=' + cloudfrontDomain,
                    }]
                },
            };
        if (expired){
            console.log("the cookie is expired");
            response.headers['set-cookie'] = [{ key: 'Set-Cookie', value: "token=; Expires=" + new Date(0).toUTCString() + "; Max-Age=-1; Secure; HttpOnly; SameSite=None;"}];
        }
            console.log("Sending cognito redirect")
            callback(null, response);
    }

    function returnSSORedirect(expired){
         var response = {
                status: '302',
                statusDescription: 'Found',
                 headers: {
                    location: [{
                         key: 'Location',
                          value: authDomain + '/oauth2/authorize?identity_provider=' + pingfedEnvironment + '&redirect_uri=' + cloudfrontDomain + '&response_type=CODE&client_id=' + clientId + '&scope=email%20openid',
                  }]
                 },
            };
        if (expired){
            console.log("the cookie is expired");
            response.headers['set-cookie'] = [{ key: 'Set-Cookie', value: "token=; Expires=" + new Date(0).toUTCString() + "; Max-Age=-1; Secure; HttpOnly; SameSite=None;"}];
        }
            console.log("Sending cognito redirect")
            callback(null, response);
    }

    var token = "";
    function tokenCheck(value){
        if (value.includes("token")){
            token = value.split("=")[1];
            // console.log("token found: " + token);
            var jwtVal = token.split(".");
            jwtVal.forEach(decodeJWT);
            const kid = JSON.parse(hps[0])["kid"];
            if (kid == jwkList[0]["kid"]){
                jwk = jwkList[0];
                console.log("Matched Kid");
            }
            else if (kid == jwkList[1]["kid"]){
                jwk = jwkList[1];
                console.log("Matched Kid");
            }
            else{
                returnError();
            }
            var pem = jwkToPem(jwk);
            jwt.verify(token, pem, { algorithms: ['RS256'] }, function(err, decodedToken) {
                if(err) {
                    console.log("There was an error validating the token!");
                    console.log(err);
                    returnCognitoRedirect(true);
                }
                else {
                    console.log("Cognito User Checked");
                    if (request.method == "POST"){
                        request.headers["Authorization"] = [{ key: 'Authorization', value: token}]
                    }
                    callback (null, request);
                }
            });
        }
        else{
            console.log("other cookie: " + value.split("=")[0]);
        }
    }

    var hps = [];

    function decodeJWT(token){
        // create buffer from base64 string
        let binaryData = Buffer.from(token, "base64");

        // decode buffer as utf8
        let base64Dec  = binaryData.toString("utf8");
        hps.push(base64Dec);
    }

    function checkUserMFAStatus(JWTtoken,cookies){
                console.log("checkUserMFAStatus");
                var accessToken = JWTtoken.access_token;
                var authorizationToken = JWTtoken.id_token;

                const data = JSON.stringify(
                                {
                  "checkUserMFAStatus": {
                      "accessToken" : accessToken
                        }
                    }
                )

                const options = {
                    protoco: 'https',
                    hostname: ".execute-api.us-east-1.amazonaws.com",
                    port: 443,
                    path: '/prod1/zincorgre-resource/mfa',
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'Authorization': authorizationToken,
                        'x-api-key':''
                    }
                };


                const req = https.request(options, (res) => {
                    let data = '';

                    res.on('data', (chunk) => {
                        data += chunk;
                    });

                    res.on('end', () => {
                        var result = JSON.parse(data);
                        console.log(result);
                        var mfaStatus=result['body']['mfaStatus']
                        var secretCode=result['body']['secretCode']
                        console.log("MFA status for user is : "+mfaStatus);
                        console.log("secretCode for user is : "+secretCode);


                        if(!mfaStatus){
                                request = {
                                    status: '307',
                                    statusDescription: 'Temporary Redirect',
                                    headers: {
                                        location: [{
                                            key: 'Location',
                                            value: cloudfrontDomain+'/MFASetup.html?code='+secretCode+"&token="+accessToken,
                                        }],
                                        'set-cookie': [{
                                            key: 'Set-Cookie',
                                            value: cookies
                                        }],
                                        'referrer-policy': [{
                                            key: 'Referrer-Policy',
                                            value: 'same-origin'
                                        }]
                                    },
                                };
                                console.log("Sending Redirect")
                                callback(null, request);
                            }else{

                                request = {
                                status: '307',
                                statusDescription: 'Temporary Redirect',
                                headers: {
                                    location: [{
                                        key: 'Location',
                                        value: cloudfrontDomain,
                                    }],
                                    'set-cookie': [{
                                        key: 'Set-Cookie',
                                        value: cookies
                                    }],
                                    'referrer-policy': [{
                                        key: 'Referrer-Policy',
                                        value: 'same-origin'
                                    }]
                                },
                            };
                            console.log("Sending Redirect")
                            callback(null, request);

                            }

                     });
                }).on("error", (err) => {
                    console.log("Error: ", err.message);
                    //returnError();
                });

                req.write(data);
                req.end();

    }

    var atcsInternalIPS = [];
    var indexOf2 = atcsInternalIPS.indexOf(IP);

    // var whiteListIPS =["100.11.90.113", "24.90.202.171", "155.91.28.240"];
    // var indexOf = whiteListIPS.indexOf(IP);
    // if ( !(indexOf2!=-1 || indexOf!=-1)){
    //   console.log("Blocked Request:");
    //   returnError();
    // }

    if(request.method == "GET"){
        if (request.uri == "/logout"){
            console.log("Logout Request");
            var response = {
                status: '302',
                statusDescription: 'Found',
                headers: {
                    location: [{
                        key: 'Location',
                        // value: authDomain + '/logout?client_id=' + clientId + '&response_type=code&scope=email+openid&redirect_uri=' + cloudfrontDomain,
                        value: cloudfrontDomain + '/Logout.html'
                    }],
                    'set-cookie': [{ key: 'Set-Cookie', value: "token=; Expires=" + new Date(0).toUTCString() + "; Max-Age=-1; Secure; HttpOnly; SameSite=None;"}]
                },
            };
            console.log("Sending cognito redirect", response)
            callback(null, response);
        }
        else if (request.uri == "/login"){
            console.log("SSO Login Request");
            //returnSSORedirect(false);
            returnCognitoRedirect(false);
        }
        else if (request.headers.cookie != undefined){
            var cookieList = request.headers.cookie[0].value.split(";");
            cookieList.forEach(tokenCheck);
            if (token == ""){
                console.log("No token found")
                //returnSSORedirect(false);
                returnCognitoRedirect(false);
            }
        }
        else if (publicList.includes(request.uri)){
           console.log("Rejected page components requested");
            callback(null, request);
        }
        else if (request.uri == "/admin"){
            console.log("Admin Login Request");
            returnCognitoRedirect(false);
        }
        else if (request.uri == "/"){
            if (request.querystring.includes("code")){
                console.log("Cognito Login");
                const code = request.querystring.split("code=")[1];

                const data = "grant_type=authorization_code&client_id=" + clientId + "&code=" + code + "&redirect_uri=" + cloudfrontDomain

                const options = {
                    protoco: 'https',
                    hostname: authDomain.split('https://')[1],
                    port: 443,
                    path: '/oauth2/token',
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'Authorization': 'Basic ' + auth
                    }
                };


                const req = https.request(options, (res) => {
                    let data = '';

                    res.on('data', (chunk) => {
                        data += chunk;
                    });

                    res.on('end', () => {
                        var JWTtoken = JSON.parse(data);
                        console.log(JWTtoken);
                        if (Object.keys(JWTtoken).includes("id_token")){
                            var jwt = JWTtoken.id_token.split(".");
                            jwt.forEach(decodeJWT);
                            console.log("Successful Cognito Authentication! User: " + hps[1]);
                            const cookies = ["token=" + JWTtoken.id_token + "; Expires=" + (new Date(JSON.parse(hps[1])["exp"]*1000)).toUTCString() + "; Max-Age=" + (JSON.parse(hps[1])["exp"]-Math.round(new Date().getTime() / 1000)-30).toString() + "; Secure; HttpOnly; SameSite=None;"];
                            //console.log(cookies[0]);
                           request = {
                                status: '307',
                                statusDescription: 'Temporary Redirect',
                                headers: {
                                    location: [{
                                        key: 'Location',
                                        value: cloudfrontDomain,
                                    }],
                                    'set-cookie': [{
                                        key: 'Set-Cookie',
                                        value: cookies
                                    }],
                                    'referrer-policy': [{
                                        key: 'Referrer-Policy',
                                        value: 'same-origin'
                                    }]
                                },
                            };
                            console.log("Sending Redirect")
                            callback(null, request);
                        }
                    });

                }).on("error", (err) => {
                    console.log("Error: ", err.message);
                    returnError();
                });

                req.write(data);
                req.end();
                }
                else if(request.querystring == ssoRejectQuerystring){
                   console.log("Single Sign-On Rejected!");
                   request.uri = "/Rejection.html";
                   callback(null, request);
                }
                else{
                    console.log("Login to main directory made: no code or cookies ");
                    console.log("Old code commented for sso");

                    //returnSSORedirect(false);
                    returnCognitoRedirect(false);
                }
        }
        else{
            console.log("No Cookies Found");
            //returnSSORedirect(false);
            returnCognitoRedirect(false);
            }
        }
    else if(request.method == "POST" && request.uri == "/api"){
        if (request.headers.cookie != undefined){
            var cookieList = request.headers.cookie[0].value.split(";");
            cookieList.forEach(tokenCheck);
            if (token == ""){
                console.log("No token found")
                //returnSSORedirect(false);
                returnCognitoRedirect(false);
            }
        }
        else{
            returnError();
        }
    }
    else{
        returnError();
    }
};
