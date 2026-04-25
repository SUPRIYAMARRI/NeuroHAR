from django.urls import path

from . import views

urlpatterns = [path("index.html", views.index, name="index"),
	             path("UserLogin.html", views.UserLogin, name="UserLogin"),
		     path("Register.html", views.Register, name="Register"),
		     path("RegisterAction", views.RegisterAction, name="RegisterAction"),
		     path("UserLoginAction", views.UserLoginAction, name="UserLoginAction"),
		     path("AdminLogin.html", views.AdminLogin, name="AdminLogin"),
		     path("AdminLoginAction", views.AdminLoginAction, name="AdminLoginAction"),
		     path("LoadDataset.html", views.LoadDataset, name="LoadDataset"),
		     path("LoadDatasetAction", views.LoadDatasetAction, name="LoadDatasetAction"),
		     path("TrainML", views.TrainML, name="TrainML"),
		     path("PredictFile", views.PredictFile, name="PredictFile"),
		     path("PredictFileAction", views.PredictFileAction, name="PredictFileAction"),
		     path("PredictParam", views.PredictParam, name="PredictParam"),
		     path("PredictParamAction", views.PredictParamAction, name="PredictParamAction"),		     
		    ]