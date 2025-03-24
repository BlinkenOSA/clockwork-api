from rest_framework.views import APIView


class CreateDigitalObject(APIView):
    """
        Create a Digital Object and give back the data.
    """
    def post(self, request, level, digital_object_id):
        pass