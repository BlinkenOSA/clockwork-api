from django.db import models


# Create your models here.
class Researcher(models.Model):
    id = models.AutoField(primary_key=True)
    card_number = models.IntegerField()
    token = models.CharField(models)
    first_name
    last_name
    middle_name
    address_hungary
    address_abroad
    city_hungary
    city_abroad
    country
    state
    id_number
    email
    citizenship
    is_student
    is_staff
    research_subject
    research_will_be_published
    date_is_tentative

    class Meta:
        db_table = 'research_researcher'