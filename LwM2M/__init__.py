from aiocoap.transports.tinydtls import DTLSClientConnection
from aiocoap import Context, Message, GET, PUT
import asyncio
import Utils


# DTLS Configuration
dtls_params = {"psk": b"psk_identity", "pskId": b"psk_key"}


class LwM2MClient:
    def __init__(self, server_uri):
        self.server_uri = server_uri

    async def bootstrap(self):
        context = await Context.create_client_context()
        context.client_credentials.load_from_dict(
            {
                self.server_uri: {
                    "dtls": DTLSClientConnection(
                        host=b"leshan.eclipseprojects.io",
                        port=5684,
                        **dtls_params,
                        coaptransport=context,
                    )
                }
            }
        )

        request = Message(code=GET, uri=self.server_uri)
        response = await context.request(request).response
        print("Bootstrap response: %s\n%r" % (response.code, response.payload))

    async def read_resource(self, path):
        context = await Context.create_client_context()
        request = Message(code=GET, uri=f"{self.server_uri}/{path}")
        response = await context.request(request).response
        print("Resource response: %s\n%r" % (response.code, response.payload))

    async def write_resource(self, path, payload):
        context = await Context.create_client_context()
        request = Message(code=PUT, uri=f"{self.server_uri}/{path}", payload=payload)
        response = await context.request(request).response
        print("Write response: %s\n%r" % (response.code, response.payload))


# Main function to run the client
async def main():
    client = LwM2MClient("coaps://leshan.eclipseprojects.io:5684")
    await client.bootstrap()
    await client.read_resource("3/0/0")  # Example path for Device object
    await client.write_resource("3/0/0", b"new_value")


if __name__ == "__main__":
    Utils.setup_logging()

    asyncio.run(main())

    Utils.end_logging()
