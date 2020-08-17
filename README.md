# Clever Counsel Serverless Crawler

This is a small microservice intended to be used along with Clever Counsel. Essentially we create a serverless REST API with Chalice and are able to hit specific endpoints on the API to make AWS Lambda functions perform actions for us.

- Specifically, we are interested in having the AWS Lambda perform Selenium related tasks like taking screenshots of full webpages in headless Chrome.
  - https://levelup.gitconnected.com/chromium-and-selenium-in-aws-lambda-6e7476a03d80

# Technologies
- AWS Lambda
  - https://aws.amazon.com/lambda/
- Chalice
  - https://chalice.readthedocs.io/en/stable/api.html

# Setup
1.  Create a venv and install all the requirements
```python
# install Python dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
2. Add AWS keys
```
$ mkdir ~/.aws
$ cat >> ~/.aws/config
[default]
aws_access_key_id=YOUR_ACCESS_KEY_HERE
aws_secret_access_key=YOUR_SECRET_ACCESS_KEY
region=YOUR_REGION (such as us-west-2, us-west-1, etc)
```
3. Run `chalice local`. This will set up a local server on localhost:8000 by default. You will need to have this running in the background whenever you wish to do anything involving "Check SOS" in the main `clever-counsel` app.
