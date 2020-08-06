from chalice import Chalice
from web_capture import capture_sos, capture_locality

app = Chalice(app_name="clever-counsel-lambda")

# change this into a post eventually


@app.route("/sos")
def take_sos_screenshot():
    """ Runs sos webcapture fxns with Selenium/Chromedriver 
        current_request: {
            entity_number, # CA SOS entity number
            intake_id 
        }
    """
    request = app.current_request
    print(request.json_body)
    data = request.json_body
    resp = capture_sos(**data)
    print(resp)
    if resp.get("success"):
        # let the main API know that you"ve completed the task
        return {"data": resp, "status": 200}
    # else, you failed somehow
    return {"status": 400}


@app.route("/locality")
def get_locality():
    """ Runs locality webcapture fxn  with Selenium/Chromedriver """
    
    data = app.current_request.json_body
    print(data)
    resp = capture_locality(**data)
    print(resp)

    # TODO: add error handling
    return {"data": resp, "status": 200}

@app.route("/test")
def test():
    """ Runs locality webcapture fxn  with Selenium/Chromedriver """
    return {"hello": "friend"}


# @app.route("/screenshot")
# def take_screenshot():


# The view function above will return {"hello": "world"}
# whenever you make an HTTP GET request to "/".
#
# Here are a few more examples:
#
# @app.route("/hello/{name}")
# def hello_name(name):
#    # "/hello/james" -> {"hello": "james"}
#    return {"hello": name}
#
# @app.route("/users", methods=["POST"])
# def create_user():
#     # This is the JSON body the user sent in their POST request.
#     user_as_json = app.current_request.json_body
#     # We"ll echo the json body back to the user in a "user" key.
#     return {"user": user_as_json}
#
# See the README documentation for more examples.
#
