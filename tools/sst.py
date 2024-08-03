
def send_link(params, user_id, role_id):
    return {"display": "https://prevencion-riesgoslaborales.com/riesgos-laborales-de-un-arquitecto#:~:text=Los%20arquitectos%20suelen%20pasar%20largas,causar%20lesiones%20a%20largo%20plazo."}


def sst_tools():
    tools = [
        {
            "type": "function",
            "function": {
                "name": "send_link",
                "description": "Send the link of the health risks of an architect",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "The name of the user"
                        }
                    },
                    "required": ["name"]
                }
            }
        }
    ]

    available_functions = {
        "send_link": send_link
    }

    return tools, available_functions