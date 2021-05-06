# Clever Counsel Serverless Crawler

This is a small microservice which can crawl specific pages, take screenshots of
those pages, and store the images in an AWS S3 bucket.

Specifically, we are interested in having the AWS Lambda perform Selenium related tasks like taking screenshots of full webpages in headless Chrome.
  - https://levelup.gitconnected.com/chromium-and-selenium-in-aws-lambda-6e7476a03d80

# Technologies
- AWS Lambda
  - https://aws.amazon.com/lambda/
- Chalice
  - https://chalice.readthedocs.io/en/stable/api.html
- Selenium
  - https://www.selenium.dev/

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

## 1.  Create a venv and install all the requirements

```sh
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 2. Download chromedriver

In order for Selenium to be able to open up Chrome in a headless environment,
you will need to download
[ChromeDriver](https://sites.google.com/a/chromium.org/chromedriver/downloads).
Try to match the version to what's in `requirements.txt`. If you need to upgrade
the requirements, please submit a PR.

## 3. Set Up AWS
### Create an S3 Bucket

When running properly, the app will store data in an S3 bucket in development
mode, and requires an access key and secret access key in order to function.
This step assumes you don't have keys and need to generate them; if you have
keys, please skip to step 3.

First, you will need to create an AWS account: https://aws.amazon.com/.

Then, create an S3 bucket (under Services > Storage). Give it a name and keep
all of the defaults.

### Create a User

Next, you'll need to create a user and give that user permission to access
your bucket. Click on your AWS username in the nav, then select "My Security
Credentials." In the side nav, under "Access Management," click on "Users," then
click on the "Add User" button.

Give the user a name and click the box to give them programmatic access.

When you get to the permissions step, click on the box labelled "Attach existing
policies directly," and select "AmazonS3FullAccess."

Click through the next steps to create the user.

### Store your AWS keys

Complete the following commands to store the AWS keys for the user you just
created. The Chalice config assumes that the profile in your config file is
`lambda_selenium`.

To create your config file:

```sh
$ mkdir ~/.aws
$ cat >> ~/.aws/config
```

Once in your config file, add the following to the bottom of the file: 

```
[profile lambda_selenium]
aws_access_key_id=YOUR_ACCESS_KEY_HERE
aws_secret_access_key=YOUR_SECRET_ACCESS_KEY
region=YOUR_BUCKET_REGION (such as us-west-2, us-west-1, etc)
```

# Running locally

```sh
chalice local
```

This will set up a local server on `localhost:8000` by default. You can now test
the app out using curl, Insomnia, or your preferred tool to assist in making
HTTP requests. At this stage, you should be able to successfully ping all three
endpoints, using the sample data provided above.

# Deployment

## Configuration

In order to have the appropriate permissions to deploy your lambda and have it
work in production, we need to add a policy to your AWS user. Head back into the
AWS console, and in the nav select click the dropdown next to your account name
and select "My Security Credentials." Next, in the side nav under "Access
Management," click on users, select your user, and click on "Add inline policy"
at the far right.

On the next page, click on the JSON tab and paste in the following policy.

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "VisualEditor0",
            "Effect": "Allow",
            "Action": [
                "apigateway:POST",
                "apigateway:GET"
            ],
            "Resource": [
                "arn:aws:apigateway:YOUR_REGION_HERE::/restapis/*",
                "arn:aws:apigateway:YOUR_REGION_HERE::/restapis/*/resources",
                "arn:aws:apigateway:YOUR_REGION_HERE::/restapis/LAMBDA_API_BASE_URL"
            ]
        },
        {
            "Sid": "VisualEditor1",
            "Effect": "Allow",
            "Action": "apigateway:DELETE",
            "Resource": "arn:aws:apigateway:YOUR_REGION_HERE::/restapis/*/resources/*"
        },
        {
            "Sid": "VisualEditor2",
            "Effect": "Allow",
            "Action": "apigateway:POST",
            "Resource": [
                "arn:aws:apigateway:YOUR_REGION_HERE::/restapis/*/deployments",
                "arn:aws:apigateway:YOUR_REGION_HERE::/restapis/*/resources/*"
            ]
        },
        {
            "Sid": "VisualEditor3",
            "Effect": "Allow",
            "Action": "apigateway:PUT",
            "Resource": [
                "arn:aws:apigateway:YOUR_REGION_HERE::/restapis/*/methods/GET",
                "arn:aws:apigateway:YOUR_REGION_HERE::/restapis/*/methods/GET/*",
                "arn:aws:apigateway:YOUR_REGION_HERE::/restapis/*/methods/POST",
                "arn:aws:apigateway:YOUR_REGION_HERE::/restapis/*/methods/POST/*",
                "arn:aws:apigateway:YOUR_REGION_HERE::/restapis/*/methods/PUT",
                "arn:aws:apigateway:YOUR_REGION_HERE::/restapis/*/methods/PUT/*",
                "arn:aws:apigateway:YOUR_REGION_HERE::/restapis/*"
            ]
        },
        {
            "Sid": "VisualEditor4",
            "Effect": "Allow",
            "Action": "apigateway:PATCH",
            "Resource": "arn:aws:apigateway:YOUR_REGION_HERE::/restapis/*"
        },
        {
            "Sid": "VisualEditor5",
            "Effect": "Allow",
            "Action": [
                "iam:GetRole",
                "iam:PassRole",
                "iam:DetachRolePolicy",
                "iam:DeleteRolePolicy",
                "lambda:*",
                "iam:CreateRole",
                "iam:AttachRolePolicy",
                "iam:PutRolePolicy"
            ],
            "Resource": "*"
        },
        {
            "Sid": "VisualEditor6",
            "Effect": "Allow",
            "Action": "execute-api:Invoke",
            "Resource": [
                "arn:aws:execute-api:YOUR_REGION_HERE:AWS_ACCOUNT_ID:LAMBDA_API_BASE_URL/api/POST/locality",
                "arn:aws:execute-api:YOUR_REGION_HERE:AWS_ACCOUNT_ID:LAMBDA_API_BASE_URL/api/POST/sos",
                "arn:aws:execute-api:YOUR_REGION_HERE:AWS_ACCOUNT_ID:LAMBDA_API_BASE_URL/api/GET/test"
            ]
        }
    ]
}
```

Be sure to replace `YOUR_REGION_HERE` with the region associated to your aws
profile, `AWS_ACCOUNT_ID` with your aws account number, and
`LAMBDA_API_BASE_URL` with the base url for your lambda function. You can find
your `AWS_ACCOUNT_ID` by clicking on the dropdown next to your username in the
nav of the AWS dashboard, and you can find the `LAMBDA_API_BASE_URL` by typing

```sh
chalice url --stage prod
```

in your terminal.

## Running a deploy

Run `chalice deploy --stage prod --profile lambda_selenium` to attempt a deploy. 

If the deployment is successful, you should see a message like this in the
terminal:

```sh
Resources deployed:
  - Lambda ARN: arn:aws:lambda:{YOUR_REGION_HERE}:{AWS_ACCOUNT_ID}:function:clever-counsel-lambda-prod
  - Rest API URL: https://{LAMBDA_API_BASE_URL}.execute-api.{YOUR_REGION_HERE}.amazonaws.com/api/
```

you should then be able to test your lambda function like so:

```sh
curl https://{LAMBDA_API_BASE_URL}.execute-api.{YOUR_REGION_HERE}.amazonaws.com/api/test
hello # if you see this, it works
```

Try it out in Insomnia as well!

## Routes requiring Auth

The test route requires no authentication, but the other routes require you to
provide your AWS credentials. The easiest way to test these endpoints is with Insomnia.

To make an authenticated request in Insomnia, enter the appropriate url (e.g. a
POST to `/sos`), the appropriate JSON data for that endpoint (see above), and
then click on the "Auth" tab and select AWS IAM v4. Fill out the Access Key ID,
Secret Access Key, and Region with the data from your config file. After that,
you should be able to test the two protected routes from within Insomnia as
well.


