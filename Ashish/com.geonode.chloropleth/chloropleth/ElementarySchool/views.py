# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render_to_response,HttpResponse,Http404,HttpResponseRedirect,render
from .models import district_boundaries,taluka_boundaries,state_maharashtra,SchoolInfo
from django.core.serializers import serialize
from colour import Color
from django.db.models import Count,Sum
from .forms import AttributeForm
import json


def get_base_map(request):
    district = state_maharashtra.objects.all().order_by('district')
    # serialize the data
    district_serialize = serialize('geojson', district,
                                   geometry_field='geom',
                                   fields=('district',))
    dist_json = json.loads(district_serialize)
    # remove crs field
    dist_json.pop('crs', None)
    district = json.dumps(dist_json)

    return render_to_response('chloropleth/maps.html', {'district': district,'name':"Base Map"})


# Create your views here.
def get_map(request,feature):
    district = state_maharashtra.objects.all().order_by('district')

    #serialize the data
    district_serialize = serialize('geojson', district,
          geometry_field='geom',
          fields=('district',))

    #create a dictionary
    max_v = 0
    min_v = 1000
    dist_json = json.loads(district_serialize)
    # remove crs field
    dist_json.pop('crs',None)
    for i in range(len(district)):
        d_name = dist_json['features'][i]['properties']['district']
        features = SchoolInfo.objects.values(str(feature)).filter(distname__iexact = d_name).aggregate(Sum(str(feature)))

        if(min_v > features[str(feature)+'__sum']):
            min_v = features[str(feature)+'__sum']
        if (max_v < features[str(feature) + '__sum']):
            max_v = features[str(feature) + '__sum']

        rag = max_v - min_v

        dist_json['features'][i]['properties']['feature_val'] = features[str(feature)+'__sum']
    district = json.dumps(dist_json)

    grade = [round(float(i*rag)/100,2) for i in range(0,110,20)]
    color_list = list(str(i) for i in Color('yellow').range_to(Color('red'), len(grade)))
    return render_to_response('chloropleth/maps.html',{'district':district,'Name':str(feature),'range':rag,
                                                       'grade':grade,'color':color_list})

def Water(request):

    try:
        dark_blue = Color('darkblue')
        light_blue = Color('lightblue')
        color_list = list(str(i) for i in light_blue.range_to(dark_blue,5))

        #Get districts shape
        district = state_maharashtra.objects.all().order_by('district')

        # serialize the data
        district_serialize = serialize('geojson', district,
                                       geometry_field='geom',
                                       fields=('district',))
        # create a dictionary
        dist_json = json.loads(district_serialize)

        # remove crs field
        dist_json.pop('crs', None)

        max_v = 0
        min_v = 1000
        weights = ['', 0, 0, 0, 1, 0]

        for i in range(len(district)):
            d_name = dist_json['features'][i]['properties']['district']
            water_info = SchoolInfo.objects.values('water').annotate(Count('water')).filter(distname__iexact=d_name).order_by('water')

            weighted_values = list()
            for x in water_info:
                if (x.get('water')) is not None:
                    if (int(x.get('water')) == 9):
                        continue
                weighted_values.append(round(weights[int(x.get('water'))] * x.get('water__count'),3))
                temp = round(sum(weighted_values) / len(weighted_values),2)
                if (temp>max_v):
                    max_v = temp
                if (temp<min_v):
                    min_v = temp
            dist_json['features'][i]['properties']['feature_val'] = temp
        district = json.dumps(dist_json)
        range_value = max_v - min_v
        feature = "Drinking Water"
        grade = [round(float(i * range_value) / 100, 2) for i in range(0, 110, 20)]
        return render_to_response('chloropleth/maps.html',{'district':district,'Name':str(feature),'range':range_value,
                                                       'grade':grade,'color':color_list})
    except IndexError ,e:
        raise Http404("Nope")

def Sanitation(request):
    try:
        sanitation_cols = ['toiletb_func', 'urinals_b', 'toiletg_func', 'urinals_g']
        # these 2 attributes are yet to be considered
        extra = ['toiletwater_b', 'toiletwater_g']

        # dist_weight contain key as district and value as its overall count of toilets
        dist_weight = dict()

        # Get districts shape
        district = state_maharashtra.objects.all().order_by('district')

        # serialize the data
        district_serialize = serialize('geojson', district,
                                       geometry_field='geom',
                                       fields=('district',))
        # create a dictionary
        dist_json = json.loads(district_serialize)

        # remove crs field
        dist_json.pop('crs', None)

        for i in range(len(district)):
            d_name = dist_json['features'][i]['properties']['district']
            # vals_dict contains all 4 attributes and handwash_yn and their total for the particular district
            vals_dict = dict()

            for col in sanitation_cols:
                vals = [x.get(col) for x in SchoolInfo.objects.values(col).filter(distname__iexact=d_name)]
                sum_of_vals = sum([int(x) for x in vals])
                vals_dict.update({col: sum_of_vals})

            # for handwash_yn, 1 = yes and 2 = no. so considering sum of total 1s
            vals_dict['handwash_yn'] = SchoolInfo.objects.values('handwash_yn').annotate(Count('handwash_yn')).\
                filter(distname__iexact=d_name).order_by('handwash_yn')[0].get('handwash_yn__count')
            dist_weight.update({d_name: sum(vals_dict.values())})
            dist_json['features'][i]['properties']['feature_val'] = sum(vals_dict.values())

        range_value = max(dist_weight.values()) - min(dist_weight.values())
        district = json.dumps(dist_json)
        grade = [round(float(i * range_value) / 100, 2) for i in range(0, 110, 20)]
        dark_blue = Color('#F0DC82')
        light_blue = Color('#8A3324')
        color_list = list(str(i) for i in light_blue.range_to(dark_blue, 5))
        feature = "Sanitation"
        return render_to_response('chloropleth/maps.html',{'district':district,'Name':str(feature),'range':range_value,
                                                       'grade':grade,'color':color_list})
    except IndexError:
        raise Http404('Nope')


def Security(request):
    try:
        # for reference
        labels = ['Not Applicable', 'Pucca', 'Pucca but broken', 'barbed wire fencing', 'Hedges',
                  'No boundary wall', 'others', 'Partial', 'Under Construction']
        # weights corresponds to the labels above
        weights = ['',0.1, 0.6, 0.4, 0.8, 0.7, 0, 0.3, 0.5, 0.2]
        # dist_weight contain key as district and value as its overall weighted average of bndry walls
        dist_weight = dict()

        district = state_maharashtra.objects.all().order_by('district')

        # serialize the data
        district_serialize = serialize('geojson', district,
                                       geometry_field='geom',
                                       fields=('district',))
        # create a dictionary
        dist_json = json.loads(district_serialize)

        # remove crs field
        dist_json.pop('crs', None)

        for i in range(len(district)):
            d_name = dist_json['features'][i]['properties']['district']
            bndry_info = SchoolInfo.objects.values('bndrywall'). \
                annotate(Count('bndrywall')).filter(distname__iexact=d_name).order_by('bndrywall')
            # vals_dict contains (total count of labels[i])*weights[i] for the particular district
            vals_dict = list()
            for x in bndry_info:
                vals_dict.append(weights[int(x.get('bndrywall'))] * x.get('bndrywall__count'))

            dist_weight.update({d_name: round(sum(vals_dict) / len(vals_dict), 2)})
            dist_json['features'][i]['properties']['feature_val'] = round(float(sum(vals_dict)) / len(vals_dict), 2)

        range_value = max(dist_weight.values()) - min(dist_weight.values())
        district = json.dumps(dist_json)
        grade = [round(float(i * range_value) / 100, 2) for i in range(0, 110, 20)]
        dark_blue = Color('#FAE6FA')
        light_blue = Color('#9F00C5')
        color_list = list(str(i) for i in light_blue.range_to(dark_blue, 5))
        feature = "Security"
        return render_to_response('chloropleth/maps.html',
                                  {'district': district, 'Name': str(feature), 'range': range_value,
                                   'grade': grade, 'color': color_list})
    except IndexError ,e:
        print str(e)
        raise Http404('Nope')


def get_features(request):
    form = AttributeForm()
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = AttributeForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            print form.cleaned_data
            return HttpResponseRedirect('/thanks/')

    # if a GET (or any other method) we'll create a blank form
    else:
        form = AttributeForm()

    return render(request,'chloropleth/form.html',{'form':form})