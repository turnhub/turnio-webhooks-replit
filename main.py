from flask import Flask
import ddg3
import os
import requests

app = Flask('app')

TOKEN = os.environ.get("TOKEN")

def search(text):
    result = ddg3.query(text)
    search_results = []
    if result.abstract.text:
        search_results.append(
            {
                "type": "TEXT",
                "body": result.abstract.text,
                "title": "Main Abstract",
                "confidence": 1.0,
            }
        )

    if result.results:
        search_results.extend(
            [
                {
                    "type": "TEXT",
                    "body": "%s - %s" % (r.text, r.url),
                    "title": "Search Result %s" % (index,),
                    "confidence": ((len(result.results) - index) / 10),
                }
                for index, r in enumerate(result.results)
            ]
        )
    return search_results


@app.route('/')
def index():
  return 'The Turn Webhook API endpoint is at /webhook'

@app.route('/webhook', methods=["POST"])
def webhook():
    from flask import request
    json = request.json
    if "statuses" in json:
        return ""

    wa_id = json["contacts"][0]["wa_id"]
    [message] = json["messages"]

    if message["type"] != "text":
        return ""

    message_id = message["id"]
    text = message["text"]["body"]

    results = search(text)
    if results:
        response = requests.post(
          url="https://whatsapp.turn.io/v1/messages",
          headers={
              "Authorization": f"Bearer {TOKEN}",
              "Content-Type": "application/json",
          },
          json={
              "to": wa_id,
              "text": {
                  "body": "\n\n".join(
                      ["*%(title)s*\n\n%(body)s" % result for result in results]
                  )
              },
          },
        ).json()
    else:
        response = requests.post(
          url="https://whatsapp.turn.io/v1/messages",
          headers={
              "Authorization": f"Bearer {TOKEN}",
              "Content-Type": "application/json",
          },
          json={
              "to": wa_id,
              "text": {
                  "body": "Apologies, DuckDuckGo did not return an abstract for %s" % (text,)
              },
          },
        ).json()
    print(response)

    response = requests.post(
        url=f"https://whatsapp.turn.io/v1/messages/{message_id}/labels",
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Accept": "application/vnd.v1+json",
            "Content-Type": "application/json",
        },
        json={"labels": ["question"]},
    )
    print(response)

    return ""


app.run(host='0.0.0.0', port=8080)