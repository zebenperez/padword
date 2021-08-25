from django.forms import Form, ImageField

class ImageUploadForm(Form):
    image = ImageField()

