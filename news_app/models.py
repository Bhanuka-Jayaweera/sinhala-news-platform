from django.db import models

# Create your models here.
class News(models.Model):
    news_id = models.CharField(max_length=50, unique=True)
    date = models.DateTimeField()
    heading = models.TextField()
    category = models.CharField(max_length=50)
    link_to_source = models.TextField()
    abstract = models.TextField()
