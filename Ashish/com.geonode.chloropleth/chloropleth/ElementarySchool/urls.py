
from django.conf.urls import url
from django.contrib import admin
from .views import get_map,Water,get_features,get_base_map,Sanitation,Security
app_name= 'district'
urlpatterns = [
    url(r'^teachers$',get_map,{'feature':'ppteacher'},name="plot_ppteacher"),
    url(r'^students$',get_map,{'feature':'ppstudent'},name="plot_ppstudent"),
    url(r'^water$',Water,name="plot_water"),
    url(r'^sanitation$',Sanitation,name="plot_sanitation"),
    url(r'^security$',Security,name="plot_security"),
    url(r'^form$',get_features,name="get_feature"),
    url(r'^$',get_base_map,name="base_map"),
]