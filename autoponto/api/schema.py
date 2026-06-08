from drf_spectacular.extensions import OpenApiAuthenticationExtension


class EdgeNodeTokenAuthenticationScheme(OpenApiAuthenticationExtension):
    target_class = "api.authentication.EdgeNodeTokenAuthentication"
    name = "EdgeNodeTokenAuth"

    def get_security_definition(self, auto_schema):
        return {
            "type": "apiKey",
            "in": "header",
            "name": "Authorization",
            "description": "Use `NodeToken <token>` no cabeçalho Authorization.",
        }
