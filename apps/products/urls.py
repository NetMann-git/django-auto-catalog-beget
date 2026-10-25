# apps/products/urls.py
from django.urls import path
from . import views, gallery_management
from .encar_import.views import import_encar
from .encar_import.package_views import package_thumbnail
from . import category_management
from . import car_model_management
from . import attribute_management

app_name = "catalog"

urlpatterns = [
    path("manage/import-encar/photo/<str:token>/<int:index>/", package_thumbnail, name="package_thumbnail"),
    path("manage/import-encar/", import_encar, name="import_encar"),
    path("", views.catalog, name="catalog"),
    
    # Маршруты сравнения (должны быть ПЕРЕД <slug:slug>/)
    path("comparison/", views.comparison_list, name="comparison"),
    path("comparison/add/<int:product_id>/", views.add_to_comparison, name="add_to_comparison"),
    path("comparison/remove/<int:product_id>/", views.remove_from_comparison, name="remove_from_comparison"),
    path("comparison/toggle/<int:product_id>/", views.toggle_comparison_ajax, name="toggle_comparison_ajax"),
    path("clear-recently-viewed-ajax/", views.clear_recently_viewed_ajax, name="clear_recently_viewed_ajax"),
    path("recently-viewed/", views.recently_viewed_list, name="recently_viewed"),
    path("brand/<slug:slug>/", views.brand_detail, name="brand_detail"),
    
    # Управление товарами (менеджер) - ДОБАВИТЬ ЭТОТ БЛОК
    path("manage/", views.product_list_manage, name="product_list_manage"),
    path("manage/attribute-types/", attribute_management.attribute_type_list_manage,
         name="attribute_type_list_manage"),
    path("manage/attribute-types/create/", attribute_management.attribute_type_create,
         name="attribute_type_create"),
    path("manage/attribute-types/<int:type_id>/edit/",
         attribute_management.attribute_type_edit, name="attribute_type_edit"),
    path("manage/attribute-types/<int:type_id>/delete/",
         attribute_management.attribute_type_delete, name="attribute_type_delete"),
    path("manage/attribute-types/<int:type_id>/values/create/",
         attribute_management.attribute_value_create, name="attribute_value_create"),
    path("manage/attribute-types/<int:type_id>/values/<int:value_id>/edit/",
         attribute_management.attribute_value_edit, name="attribute_value_edit"),
    path("manage/attribute-types/<int:type_id>/values/<int:value_id>/delete/",
         attribute_management.attribute_value_delete, name="attribute_value_delete"),
    path("manage/categories/", category_management.category_list,
         name="category_list_manage"),
    path("manage/categories/create/", category_management.category_edit,
         name="category_create"),
    path("manage/categories/<int:category_id>/edit/",
         category_management.category_edit, name="category_edit"),
    path("manage/categories/<int:category_id>/delete/",
         category_management.category_delete, name="category_delete"),
    path("manage/car-models/", car_model_management.car_model_list, name="car_model_list"),
    path("manage/car-models/create/", car_model_management.car_model_edit, name="car_model_create"),
    path("manage/car-models/<int:model_id>/edit/", car_model_management.car_model_edit, name="car_model_edit"),
    path("manage/car-models/<int:model_id>/delete/", car_model_management.car_model_delete, name="car_model_delete"),
    path("manage/brands/", views.brand_list_manage, name="brand_list_manage"),
    path("manage/brands/create/", views.brand_create, name="brand_create"),
    path("manage/brands/<int:brand_id>/edit/", views.brand_edit, name="brand_edit"),
    path("manage/brands/<int:brand_id>/delete/", views.brand_delete, name="brand_delete"),
    path("create/", views.product_create, name="product_create"),
    path("edit/<int:product_id>/", views.product_edit, name="product_edit"),
    path("delete/<int:product_id>/", views.product_delete, name="product_delete"),
    path('attributes/<int:product_id>/', views.product_attributes, name='product_attributes'),
    path('attribute/delete/<int:attribute_id>/', views.attribute_delete, name='attribute_delete'),

    path('gallery/prepare/<int:product_id>/', gallery_management.prepare, name='gallery_prepare'),
    path('gallery/order/<int:product_id>/', gallery_management.reorder, name='gallery_order'),
    path('gallery/cover/<int:image_id>/', gallery_management.cover, name='gallery_cover'),
    # Галерея
    path('gallery/add/<int:product_id>/', gallery_management.upload, name='gallery_add'),
    path('gallery/delete/<int:image_id>/', gallery_management.delete, name='gallery_delete'),
    
    # Страница товара (должна быть последней)
    path("<slug:slug>/", views.product_detail, name="product_detail"),
]
