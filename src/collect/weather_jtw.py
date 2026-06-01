import time
import jwt


def generate_jwt(private_key, kid, project_id):
    """Generate a JWT for authentication.

    Args:
        private_key (str): The PEM-formatted private key.
        kid (str): The Key ID for the JWT header.
        project_id (str): The subject claim for the JWT.

    Returns:
        str: The encoded JWT.
    """
    payload = {
        "iat": int(time.time()) - 30,
        "exp": int(time.time()) + 900,
        "sub": project_id,
    }
    headers = {"kid": kid}

    try:
        encoded_jwt = jwt.encode(
            payload, private_key, algorithm="EdDSA", headers=headers
        )
        return encoded_jwt
    except Exception as e:
        print(f"Error generating JWT: {e}")
        return None


if __name__ == "__main__":
    import json
    import os
    from dotenv import load_dotenv

    load_dotenv(override=True)
    weather_config = json.loads(os.getenv("WEATHER_CONFIG", "{}"))
    my_private_key = weather_config.get("PRIVATE_KEY")
    my_kid = weather_config.get("JWT_KID")
    my_project_id = weather_config.get("PROJECT_ID")

    jwt_token = generate_jwt(my_private_key, my_kid, my_project_id)
    if jwt_token:
        print(f"Generated JWT: {jwt_token}")
