from django.db import models

class Products(models.Model):
    name=models.CharField(max_length=200)
    desc=models.CharField(max_length=1000)
    price=models.FloatField()
    file=models.FileField(upload_to='uploads')

    def __str__(self):
        return self.name


