# Clever Counsel Serverless Crawler

This is a small microservice intended to be used along with Clever Counsel. Essentially we create a serverless REST API with Chalice and are able to hit specific endpoints on the API to make AWS Lambda functions perform actions for us.

- Specifically, we are interested in having the AWS Lambda perform Selenium related tasks like taking screenshots of full webpages in headless Chrome.
  - https://levelup.gitconnected.com/chromium-and-selenium-in-aws-lambda-6e7476a03d80

# Technologies
- AWS Lambda
  - https://aws.amazon.com/lambda/
- Chalice
  - https://chalice.readthedocs.io/en/stable/api.html

# Usage

The app consists of three endpoints. 

### GET /test

Just returns "hello". Not very exciting.

### POST /sos

Given request data like this:

```js
{
  "entity_number": "C1437404",
  "s3_directory": "intakes/test"
}
```

The app opens up Chrome, and using Selenium it navigates to the California
Secretary of State website. It then visits the business search page
corresponding to the entity id provided (e.g.
https://businesssearch.sos.ca.gov/CBS/SearchResults?filing=&SearchType=NUMBER&SearchCriteria=C1437404)
and clicks on the business. (Note that because of the way the CA SoS website
works, we can't navigate to the business page directly.)

Once on the appropriate business page, the app takes a screenshot of the page,
uploads the screenshot to an AWS S3 bucket, and returns a link to the screenshot
along with the business address.

As a practical matter, the `s3_directory` is not too important for this
microservice. The only thing that depends on it is the folder structure of how
the images are stored in S3.

### POST /locality

Given request data like this:

```js
{
	"home_number": "926",
	"street_name": "BROXTON",
	"zip_code": "90024",
	"s3_directory": "intakes/test"
}
```

The app opens up Chrome, and using Selenium it navigates to the Los Angeles
County precints map application (https://lavote.net/apps/PrecinctsMaps/). It
then navigates through this app to retrieve the "locality" corresponding to the
address provided. This is useful information that is not obtainable from the
Secretary of State website.

As with the `/sos` endpoint, the route handler takes a screenshot of the page
where the locality information is found, and uploads it to the same S3 bucket in
the provided `s3_directory`.

# Setup
1.  Create a venv and install all the requirements

```sh
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Configure AWS
When running properly, the app will 

```
$ mkdir ~/.aws
$ cat >> ~/.aws/config
[default]
aws_access_key_id=YOUR_ACCESS_KEY_HERE
aws_secret_access_key=YOUR_SECRET_ACCESS_KEY
region=YOUR_REGION (such as us-west-2, us-west-1, etc)
```
3. Run `chalice local`. This will set up a local server on localhost:8000 by default. You will need to have this running in the background whenever you wish to do anything involving "Check SOS" in the main `clever-counsel` app.

# Try it out

