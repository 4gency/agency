# TODO: make this function
# def create_default_pod_configuration(bot_id: str, api_key: str, image: str) -> dict:
#     return {
#         "apiVersion": "v1",
#         "kind": "Pod",
#         "metadata": {"name": f"bot-{bot_id}"},
#         "spec": {
#             "containers": [
#                 {
#                     "name": "bot",
#                     "image": "seu-repositorio/sua-imagem:latest",
#                     "env": [
#                         {"name": "API_KEY", "value": str(api_key)},
#                         {"name": "BOT_ID", "value": str(bot_id)},
#                     ],
#                 }
#             ]
#         },
#     }
