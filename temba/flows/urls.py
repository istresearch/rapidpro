from django.urls import re_path

from .views import FlowCRUDL, FlowLabelCRUDL, FlowRunCRUDL, FlowSessionCRUDL, FlowStartCRUDL, PartialTemplate

urlpatterns = FlowCRUDL().as_urlpatterns()
urlpatterns += FlowLabelCRUDL().as_urlpatterns()
urlpatterns += FlowRunCRUDL().as_urlpatterns()
urlpatterns += FlowSessionCRUDL().as_urlpatterns()
urlpatterns += FlowStartCRUDL().as_urlpatterns()
urlpatterns += [
    re_path(r"^partials/(?P<template>[a-z0-9\-_]+)$", PartialTemplate.as_view(), name="flows.partial_template")
]
