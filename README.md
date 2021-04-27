# mini-bank
Mini banking system on Flask & PostgreSQL

Test server :point_right: https://mini-bank-kuvera.herokuapp.com/foo

Register to Kuvera Bank

```
curl --location --request POST 'https://mini-bank-kuvera.herokuapp.com/register?username=yourname&email=yourname@gmail.com&password=Test@123'
```

Sign-in (A token is received in reponse which can be used to validate following APIs - Expires in 24hrs)

```
curl --location --request GET 'https://mini-bank-kuvera.herokuapp.com/sign_in?username=yourname&password=Test@123'
```

Transact

```
curl --location --request POST 'https://mini-bank-kuvera.herokuapp.com/transaction/transact' \
--header 'authtoken: 65794a30655841694f694a4b563151694c434a68624763694f694a49557a49314e694a392e65794a6c654841694f6a45324d546b314e444d344e7a6373496d6c68644349364d5459784f5451314e7a51334e79776963335669496a6f3266512e494f6b7a4e6a33424c486750575469394c326a634364644251756a45454b6c7a394a6a41747a45354f6577' \
--header 'Content-Type: application/json' \
--data-raw '{
    "amount": 5000
}'
```

Fetch Balance

```
curl --location --request GET 'https://mini-bank-kuvera.herokuapp.com/transaction/balance' \
--header 'authtoken: 65794a30655841694f694a4b563151694c434a68624763694f694a49557a49314e694a392e65794a6c654841694f6a45324d546b314e444d344d544973496d6c68644349364d5459784f5451314e7a51784d69776963335669496a6f3266512e7064654e4363584c4c75696a6a356d515977435f43504d554f744c30354231386f36775730774a626b4d6b' \
--data-raw ''
```