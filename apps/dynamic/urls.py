from django.urls import path

from .views import *

app_name = "dynamic"

urlpatterns = [
    # Why Choose Us
    path("why-list/", WhyChooseUsListViews.as_view(), name="why_list"),
    path("why-create/", WhyChooseUsCreateViews.as_view(), name="why_create"),
    path("why-update/<int:pk>/", WhyChooseUsUpdateViews.as_view(), name="why_update"),
    path("why-delete/<int:pk>/", WhyChooseUsDeleteViews.as_view(), name="why_delete"),
    
    # FAQ
    path("faq-list/", FAQListView.as_view(), name="faq_list"),
    path("faq-create/", FAQCreateView.as_view(), name="faq_create"),
    path("faq-update/<int:pk>/", FAQUpdateView.as_view(), name="faq_update"),
    path("faq-delete/<int:pk>/", FAQDeleteView.as_view(), name="faq_delete"),
    
    # about
    path("about-list/", AboutListView.as_view(), name="about_list"),
    path("about-create/", AboutCreateView.as_view(), name="about_create"),
    path("update/<int:pk>/", AboutUpdateView.as_view(), name="about_update"),
    path("delete/<int:pk>/", AboutDeleteView.as_view(), name="about_delete"),
    path("promises/", PromiseSectionListView.as_view(), name="promise_list"),
    path("promises/create/",PromiseSectionCreateView.as_view(),name="promise_section_create",),
    path("promises/<int:pk>/edit/",PromiseSectionEditView.as_view(),name="promise_section_edit",),
    path("promises/<int:pk>/delete/",PromiseSectionDeleteView.as_view(),name="promise_section_delete",),
    
    # Card URLs
    path("promises/card/save/", PromiseCardSaveView.as_view(), name="promise_card_save"),
    path("promises/card/<int:pk>/delete/",PromiseCardDeleteView.as_view(),name="promise_card_delete",),
    path("partners/", PartnerSectionListView.as_view(), name="partner_list"),
    path("partners/create/",PartnerSectionCreateView.as_view(),name="partner_section_create",),
    path("partners/update/<int:pk>/",PartnerSectionUpdateView.as_view(),name="partner_section_edit",),
    path("partners/<int:pk>/delete/",PartnerSectionDeleteView.as_view(),name="partner_section_delete",),
    path("partners/<int:section_id>/images/",PartnerImageListView.as_view(),name="partner_image_list",),
    path("partners/<int:section_id>/images/create/",PartnerImageCreateView.as_view(),name="partner_image_create",),
    path("partners/images/delete/<int:pk>/",PartnerImageDeleteView.as_view(),name="partner_image_delete",),
    path("team/", TeamListView.as_view(), name="team_list"),
    path("team/create/", TeamCreateView.as_view(), name="team_create"),
    path("team/update/<int:pk>/", TeamUpdateView.as_view(), name="team_update"),
    path("team/delete/<int:pk>/", TeamDeleteView.as_view(), name="team_delete"),
    
    # Popular Service Sections
    # path("services/", ServiceSectionListView.as_view(), name="service_list"),
    # path("services/create/",ServiceSectionCreateView.as_view(),name="service_section_create",),
    # path("services/<int:pk>/edit/",ServiceSectionUpdateView.as_view(),name="service_section_edit"),
    # path("services/<int:pk>/delete/",ServiceSectionDeleteView.as_view(),name="service_section_delete"),
    # path("services/item/save/",PopularServiceItemSaveView.as_view(),name="service_item_save"),
    # path("services/item/<int:pk>/delete/",PopularServiceItemDeleteView.as_view(),name="service_item_delete"),
    
    # Why Choose Us Section
    # path("who-we-are/", WhyChooseUsListView.as_view(), name="who_we_are_list"),
    # path("who_we_are/create/",WhyChooseUsCreateView.as_view(),name="who_we_are_create"),
    # path("who_we_are/update/<int:pk>/",WhyChooseUsUpdateView.as_view(),name="who_we_are_update"),
    # path("who_we_are/delete/<int:pk>/",WhyChooseUsDeleteView.as_view(),name="who_we_are_delete"),
    path("contact/", ContactListView.as_view(), name="contact_list"),
    path("contact/create/", ContactCreateView.as_view(), name="contact_create"),
    path("contact/update/<int:pk>/", ContactUpdateView.as_view(), name="contact_update"),
    path("contact/delete/<int:pk>/", ContactDeleteView.as_view(), name="contact_delete"),
    
    # Tourist Places
    path("place-list/", PlaceListView.as_view(), name="place_list"),
    path("place-create/", PlaceCreateView.as_view(), name="place_create"),
    path("place-update/<int:pk>/", PlaceUpdateView.as_view(), name="place_update"),
    path("place-delete/<int:pk>/", PlaceDeleteView.as_view(), name="place_delete"),
    path("who-we-are/",WhoWeAreListView.as_view(),name="who_we_are_list",),
    path("who-we-are/create/",WhoWeAreCreateView.as_view(),name="who_we_are_create",),
    path("who-we-are/<int:pk>/edit/",WhoWeAreUpdateView.as_view(),name="who_we_are_update",),
    path("who-we-are/<int:pk>/delete/",WhoWeAreDeleteView.as_view(),name="who_we_are_delete",),
    
    
    # path("who_we_are_list",WhoweareListView.as_view(),   name="who_we_are_list"),
    # path("who_we_are/create/",WhoweareCreateView.as_view(), name="who_we_are_create"),
    # path("who_we_are/<int:pk>/edit/",WhoweareEditView.as_view(),name="who_we_are_edit"),
    # path("who_we_are/<int:pk>/delete/",WhoweareDeleteView.as_view(),name="who_we_are_delete"),
    
    path('terms/', TermsListView.as_view(), name='terms_list'),
    path('terms/create/', TermsCreateView.as_view(), name='terms_create'),
    path('terms/<int:pk>/edit/', TermsUpdateView.as_view(), name='terms_update'),
    path('terms/<int:pk>/delete/', TermsDeleteView.as_view(), name='terms_delete'),

    # Privacy Mappings
    path('privacy/', PrivacyListView.as_view(), name='privacy_list'),
    path('privacy/create/', PrivacyCreateView.as_view(), name='privacy_create'),
    path('privacy/<int:pk>/edit/', PrivacyUpdateView.as_view(), name='privacy_update'),
    path('privacy/<int:pk>/delete/', PrivacyDeleteView.as_view(), name='privacy_delete'),
    
    
    path("contact-enquiries/",SuperAdminContactEnquiryView.as_view(),name="contact_enquiry_list",),

    # Popular Business Searches
    path(
        "popular-business-searches/",
        PopularBusinessSearchListView.as_view(),
        name="popular_business_searches_list",
    ),
    path(
        "popular-business-searches/<int:pk>/approve/",
        ApproveBusinessSearchView.as_view(),
        name="approve_business_search",
    ),
    path(
        "popular-business-searches/<int:pk>/reject/",
        RejectBusinessSearchView.as_view(),
        name="reject_business_search",
    ),
]
    
    
    
    
    
    
    
    
    
    
    
    