#!/usr/bin/python
# -*- coding: utf-8 -*-
from django.urls import path
from . import views, auto_views, room_views, card_views, lock_views, lock_user_views, lock_group_views 
from . import gateway_views, ekey_views, box_views, lock_cron_views, project_admin_views, project_lock_views, project_manager_views
from . import project_subadmin_views, project_satadmin_views

urlpatterns = [ 
    #path('index/<slug:chk>/', views.index, name='web-index-new'),
    path('index/', views.index, name='web-index-new'),
    path('', views.index, name='web-index'),
    path('set-project/<slug:uuid>/', views.set_project, name='set-project'),
    path('get-menus/', views.get_menus, name='get-menus'), #REMOVE
    path('set-menus/', views.set_menus, name='set-menus'), #REMOVE

    #path('stripe/test-payment/<int:test_type>', views.stripe_test_payment, name='stripe-test-payment'),
    #path('stripe/test-payment/<str:test_type>', views.stripe_test_payment, name='stripe-test-payment'),
    #path('stripe/test-payment/', views.stripe_test_payment, name='stripe-test-payment'),
    #path('stripe/alta-client/<str:uuid_guest>', views.stripe_alta_client, name='stripe-alta-client'),
    #path('stripe/store-payment/<str:session_id>', views.stripe_store_payment, name='stripe-store-payment'),
    #path('stripe/error-payment/<str:session_id>', views.stripe_error_payment, name='stripe-error-payment'),
    #path('stripe/do-payment/', views.stripe_payment, name='stripe-payment'),

    #--------------------- Projects --------------------
    path('projects/company-<int:company_id>/', views.projects, name='projects-by-company'),
    path('projects/project-<slug:project_id>/', views.projects, name='projects-by-uuid'),
    path('projects/', views.projects, name='projects'),
    path('projects/search/', views.project_search, name='project-search'),
    path('projects/form/', views.project_form, name='project-form'),
    path('projects/details/<int:obj_id>/', views.project_details, name='project-details'),
    path('projects/details/<int:obj_id>/<slug:current_tab>/', views.project_details, name='project-details'),
    path('projects/remove/', views.project_remove, name='project-remove'),
    path('projects/upload-json/', views.project_upload_json, name='project-upload-json'),
    path('projects/user-token/', views.project_user_token, name='project-user-token'),
    path('projects/user-refresh-token/', views.project_user_refresh_token, name='project-user-refresh-token'),
    path('projects/regime-toggle/', views.project_regime_toggle, name='project-regime-toggle'),
    path('projects/regime-add/', views.project_regime_add, name='project-regime-add'),
    path('projects/regime-remove/', views.project_regime_remove, name='project-regime-remove'),
    path('projects/pos-add/', views.project_pos_add, name='project-pos-add'),
    path('projects/pos-remove/', views.project_pos_remove, name='project-pos-remove'),
    path('projects/pos-cat-toggle/', views.project_pos_cat_toggle, name='project-pos-cat-toggle'),
    path('projects/pos-add-image/', views.project_pos_add_image, name='project-pos-add-image'),
    path('projects/pos-remove-image/', views.project_pos_remove_image, name='project-pos-remove-image'),
    path('projects/pos-daily-summary/<int:obj_id>/', views.project_pos_daily_summary, name='project-pos-daily-summary'),
    path('projects/table-add/', views.project_table_add, name='project-table-add'),
    path('projects/table-remove/', views.project_table_remove, name='project-table-remove'),
    path('projects/table-range/', views.project_table_range, name='project-table-range'),
    path('projects/pos-discount-add/', views.project_pos_discount_add, name='project-pos-discount-add'),
    path('projects/pos-discount-remove/', views.project_pos_discount_remove, name='project-pos-discount-remove'),
    path('projects/pos-discount-item-add/', views.project_pos_discount_item_add, name='project-pos-discount-item-add'),
    path('projects/pos-discount-item-remove/', views.project_pos_discount_item_remove, name='project-pos-discount-item-remove'),
    path('projects/invitation-add/', views.project_invitation_add, name='project-invitation-add'),
    path('projects/invitation-remove/', views.project_invitation_remove, name='project-invitation-remove'),
    path('projects/guest-types-add/', views.project_guest_types_add, name='project-guest-types-add'),
    path('projects/guest-types-remove/', views.project_guest_types_remove, name='project-guest-types-remove'),
    path('projects/access-zone-add/', views.project_access_zone_add, name='project-access-zone-add'),
    path('projects/access-zone-remove/', views.project_access_zone_remove, name='project-access-zone-remove'),
    path('projects/access-zone-close/', views.project_access_zone_close, name='project-access-zone-close'),
    path('projects/access-zone-times-add/', views.project_access_zone_times_add, name='project-access-zone-times-add'),
    path('projects/access-zone-times-remove/', views.project_access_zone_times_remove, name='project-access-zone-times-remove'),
    path('projects/access-points-add/', views.project_access_points_add, name='project-access-points-add'),
    path('projects/access-points-remove/', views.project_access_points_remove, name='project-access-points-remove'),
    path('projects/thirdpart-add/', views.project_thirdpart_add, name='project-thirdpart-add'),
    path('projects/thirdpart-remove/', views.project_thirdpart_remove, name='project-thirdpart-remove'),
    path('projects/thirdpart-toggle/', views.project_thirdpart_toggle, name='project-thirdpart-toggle'),
    path('projects/partner-add/', views.project_partner_add, name='project-partner-add'),
    path('projects/partner-remove/', views.project_partner_remove, name='project-partner-remove'),
    path('projects/set-avantio-schedule/', views.project_set_avantio_schedule, name='project-set-avantio-schedule'),
    path('projects/set-avaibook-schedule/', views.project_set_avaibook_schedule, name='project-set-avaibook-schedule'),
    path('projects/set-winhotel-schedule/', views.project_set_winhotel_schedule, name='project-set-winhotel-schedule'),
    path('projects/set-lock-schedule/', views.project_set_lock_schedule, name='project-set-lock-schedule'),
    path('projects/set-mews-schedule/', views.project_set_mews_schedule, name='project-set-mews-schedule'),
    path('projects/set-cloudbeds-schedule/', views.project_set_cloudbeds_schedule, name='project-set-cloudbeds-schedule'),
    path('projects/set-cloudbeds-webhooks/', views.project_set_cloudbeds_webhooks, name='project-set-cloudbeds-webhooks'),
    path('projects/get-cloudbeds-webhooks/', views.project_get_cloudbeds_webhooks, name='project-get-cloudbeds-webhooks'),
    path('projects/remove-cloudbeds-webhooks/', views.project_remove_cloudbeds_webhooks, name='project-remove-cloudbeds-webhooks'),
    path('projects/set-octorate-schedule/', views.project_set_octorate_schedule, name='project-set-octorate-schedule'),
    path('projects/set-cars-schedule/', views.project_set_cars_schedule, name='project-set-cars-schedule'),
    path('projects/add-logo/', views.project_add_logo, name='project-add-logo'),
    path('projects/remove-logo/', views.project_remove_logo, name='project-remove-logo'),
    
    #--------------------- Projects Admin--------------------
    path('projects-admin/', project_admin_views.projects, name='projects-admin'),
    path('projects-admin/search/', project_admin_views.projects_search, name='projects-admin-search'),
    path('projects-admin/details/<int:obj_id>/', project_admin_views.projects_details, name='projects-admin-details'),
    path('projects-admin/user-refresh-token/', project_admin_views.project_user_refresh_token,name='project-admin-user-refresh-token'),
 
    #--------------------- Projects SubAdmin--------------------
    path('projects-subadmin/', project_subadmin_views.projects, name='projects-subadmin'),
    path('projects-subadmin/search/', project_subadmin_views.projects_search, name='projects-subadmin-search'),
    path('projects-subadmin/details/<int:obj_id>/', project_subadmin_views.projects_details, name='projects-subadmin-details'),
    path('projects-subadmin/user-token/', project_subadmin_views.project_user_token, name='project-subadmin-user-token'),
    path('projects-subadmin/user-refresh-token/', project_subadmin_views.project_user_refresh_token, name='project-subadmin-user-refresh-token'),
    path('projects-subadmin/locks-by-project/<int:project_id>/', project_subadmin_views.locks_by_project, name='projects-subadmin-locks-by-project'),
    path('projects-subadmin/locks-update-params/', project_subadmin_views.lock_update_params, name='projects-subadmin-locks-update-params'),
    path('projects-subadmin/locks-get-all-passcodes/', project_subadmin_views.lock_get_all_passcodes, name='projects-subadmin-locks-get-all-passcodes'),
    path('projects-subadmin/locks-get-all-cards/', project_subadmin_views.lock_get_all_cards, name='projects-subadmin-locks-get-all-cards'),
    path('projects-subadmin/locks-get-all-records/', project_subadmin_views.lock_get_all_records, name='projects-subadmin-locks-get-all-records'),
    path('projects-subadmin/locks/form/', project_subadmin_views.lock_form, name='projects-subadmin-lock-form'),
    path('projects-subadmin/gateways-by-project/<int:project_id>/', project_subadmin_views.gateways_by_project, name='projects-subadmin-gateways-by-project'),

    #--------------------- Projects SatAdmin--------------------
    path('projects-satadmin/', project_satadmin_views.projects, name='projects-satadmin'),
    path('projects-satadmin/search/', project_satadmin_views.projects_search, name='projects-satadmin-search'),
    path('projects-satadmin/details/<int:obj_id>/', project_satadmin_views.projects_details, name='projects-satadmin-details'),
    #path('projects-satadmin/user-token/', project_satadmin_views.project_user_token, name='project-satadmin-user-token'),
    path('projects-satadmin/user-refresh-token/', project_satadmin_views.project_user_refresh_token, name='project-satadmin-user-refresh-token'),
    path('projects-satadmin/locks-by-project/<int:project_id>/', project_satadmin_views.locks_by_project, name='projects-satadmin-locks-by-project'),
    path('projects-satadmin/locks-update-params/', project_satadmin_views.lock_update_params, name='projects-satadmin-locks-update-params'),
    path('projects-satadmin/locks-get-all-passcodes/', project_satadmin_views.lock_get_all_passcodes, name='projects-satadmin-locks-get-all-passcodes'),
    path('projects-satadmin/locks-get-all-cards/', project_satadmin_views.lock_get_all_cards, name='projects-satadmin-locks-get-all-cards'),
    path('projects-satadmin/locks-get-all-records/', project_satadmin_views.lock_get_all_records, name='projects-satadmin-locks-get-all-records'),
    path('projects-satadmin/locks/form/', project_satadmin_views.lock_form, name='projects-satadmin-lock-form'),
    path('projects-satadmin/gateways-by-project/<int:project_id>/', project_satadmin_views.gateways_by_project, name='projects-satadmin-gateways-by-project'),


    #--------------------- Projects Manager--------------------
    path('projects-manager/', project_manager_views.projects, name='projects-manager'),
    path('projects-manager/search/', project_manager_views.projects_search, name='projects-manager-search'),
    path('projects-manager/details/<int:obj_id>/', project_manager_views.projects_details, name='projects-manager-details'),
    path('projects-manager/form/', project_manager_views.projects_form, name='projects-manager-form'),
    path('projects-manager/user-token/', project_manager_views.project_user_token, name='projects-manager-user-token'),
    path('projects-manager/user-refresh-token/', project_manager_views.project_user_refresh_token, name='projects-manager-user-refresh-token'),
    path('projects-manager/categories/project-<slug:project_id>/', project_manager_views.categories_by_project, name='projects-manager-categories-by-project'),

    path('projects-manager/companies/', project_manager_views.companies, name='projects-manager-companies'),
    path('projects-manager/companies/search/', project_manager_views.companies_search, name='projects-manager-companies-search'),
    path('projects-manager/companies/form/', project_manager_views.companies_form, name='projects-manager-companies-form'),

    path('projects-manager/rooms/project-<slug:project_uuid>/', project_manager_views.rooms, name='projects-manager-rooms'),
    path('projects-manager/rooms/search/', project_manager_views.rooms_search, name='projects-manager-rooms-search'),
    path('projects-manager/rooms/form/', project_manager_views.rooms_form, name='projects-manager-rooms-form'),
    path('projects-manager/rooms/remove/', project_manager_views.rooms_remove, name='projects-manager-rooms-remove'),
    path('projects-manager/rooms/multiple/', project_manager_views.rooms_multiple, name='projects-manager-rooms-multiple'),
    path('projects-manager/rooms/multiple-save/', project_manager_views.rooms_multiple_save, name='projects-manager-rooms-multiple-save'),

    #--------------------- Projects Locks--------------------
    path('projects-locks/', project_lock_views.projects, name='projects-locks'),
    path('projects-locks/search/', project_lock_views.projects_search, name='projects-locks-search'),
    path('projects-locks/details/<int:obj_id>/', project_lock_views.projects_details, name='projects-locks-details'),
    path('projects-locks/by-project/<int:project_id>/', project_lock_views.locks_by_project, name='projects-locks-by-project'),
    path('projects-locks/gateways-by-project/<int:project_id>/', project_lock_views.gateways_by_project, name='projects-locks-gateways-by-project'),
    path('projects-locks/update-params/', project_lock_views.lock_update_params, name='projects-locks-update-params'),
    path('projects-locks/get-all-passcodes/', project_lock_views.lock_get_all_passcodes, name='projects-locks-get-all-passcodes'),
    path('projects-locks/get-all-cards/', project_lock_views.lock_get_all_cards, name='projects-locks-get-all-cards'),
    path('projects-locks/get-all-records/', project_lock_views.lock_get_all_records, name='projects-locks-get-all-records'),

    #--------------------- Channels --------------------
    path('channels/project-<slug:project_id>/', views.channels, name='channels-by-project'),
    path('channels/company-<slug:company_id>/', views.channels, name='channels-by-company'),
    path('channels/', views.channels, name='channels'),
    path('channels/search/', views.channel_search, name='channel-search'),
    path('channels/form/', views.channel_form, name='channel-form'),
    path('channels/remove/', views.channel_remove, name='web-channel-remove'),
    #--------------------- Companies --------------------
    path('companies/', views.companies, name='companies'),
    path('companies/search/', views.company_search, name='company-search'),
    path('companies/form/', views.company_form, name='company-form'),
    path('companies/remove/', views.company_remove, name='company-remove'),
    #--------------------- Devices --------------------
    path('devices/project-<int:project_id>/', views.devices_by_project, name='devices-by-project'),
    path('devices/channel-<int:channel_id>/', views.devices_by_channel, name='devices-by-channel'),
    path('devices/company-<int:company_id>/', views.devices_by_project, name='devices-by-company'),
    path('devices/', views.devices, name='devices'),
    path('devices/search/', views.device_search, name='device-search'),
    path('devices/form/', views.device_form, name='device-form'),
    path('devices/assign/', views.device_assign, name='device-assign'),
    path('devices/remove/', views.device_remove, name='device-remove'),
    #--------------------- Locks --------------------
    #path('locks/', lock_views.locks, name='locks'),
    path('locks-by-project/<int:project_id>/', lock_views.locks_by_project, name='locks-by-project'),
    path('locks/row/', lock_views.lock_row, name='lock-row'),
    path('locks/search/', lock_views.lock_search, name='lock-search'),
    path('locks/form/', lock_views.lock_form, name='lock-form'),
    path('locks/remove/', lock_views.lock_remove, name='lock-remove'),
    path('locks/get-all-passcodes/', lock_views.lock_get_all_passcodes, name='lock-get-all-passcodes'),
    path('locks/remove/code/', lock_views.lock_remove_code, name='lock-remove-code'),
    path('locks/remove-all-passcodes/', lock_views.lock_remove_all_passcodes, name='lock-remove-all-passcodes'),
    path('locks/get-all-cards/', lock_views.lock_get_all_cards, name='lock-get-all-cards'),
    path('locks/remove/card/', lock_views.lock_remove_card, name='lock-remove-card'),
    path('locks/remove-all-cards/', lock_views.lock_remove_all_cards, name='lock-remove-all-cards'),
    path('locks/get-all-records/', lock_views.lock_get_all_records, name='lock-get-all-records'),
    path('locks/set-action/', lock_views.lock_set_action, name='lock-set-action'),
    path('locks/share-code/', lock_views.lock_share_code, name='lock-share-code'),
    path('locks/share-code-guest/', lock_views.lock_share_code_guest, name='lock-share-code-guest'),
    path('locks/update-params/', lock_views.lock_update_params, name='lock-update-params'),
    path('locks/set-group/', lock_views.lock_set_group, name='lock-set-group'),
    path('locks/export-csv/<int:lock_id>/', lock_views.lock_export_csv, name='lock-export-csv'),
    path('locks/export-pdf/<int:lock_id>/', lock_views.lock_export_pdf, name='lock-export-pdf'),

    path('locks/by-project/', lock_views.locks_by_project2, name='locks-by-project2'),
    path('locks/row/by-project/', lock_views.lock_row_by_project, name='lock-row-by-project'),
    path('locks/search/by-project/', lock_views.lock_search_by_project, name='lock-search-by-project'),
    path('locks/update-params/by-project/', lock_views.lock_update_params_by_project, name='lock-update-params-by-project'),
    path('locks/get-all-passcodes/by-project/', lock_views.lock_get_all_passcodes_by_project, name='lock-get-all-passcodes-by-project'),
    path('locks/get-all-cards/by-project/', lock_views.lock_get_all_cards_by_project, name='lock-get-all-cards-by-project'),
    path('locks/get-all-records/by-project/', lock_views.lock_get_all_records_by_project, name='lock-get-all-records-by-project'),
    path('locks/set-action/by-project/', lock_views.lock_set_action_by_project, name='lock-set-action-by-project'),
    path('locks/update-info/<slug:code>/', lock_views.locks_update_info, name='locks-update-info'),
    path('locks/open/', lock_views.locks_open, name='locks-open'),

    #--------------------- LocksUsers --------------------
    path('locks-users/', lock_user_views.locks_users, name='locks-users'),
    path('locks-users/search/', lock_user_views.lock_user_search, name='lock-user-search'),
    path('locks-users/form/', lock_user_views.lock_user_form, name='lock-user-form'),
    path('locks-users/set-password/', lock_user_views.lock_user_set_password, name='lock-user-set-password'),
    path('locks-users/register/', lock_user_views.lock_user_register, name='lock-user-register'),
    path('locks-users/remove/', lock_user_views.lock_user_remove, name='lock-user-remove'),
    path('locks-users/remove-by-username/', lock_user_views.lock_user_remove_by_username, name='lock-user-remove-by-username'),
    #--------------------- LocksGroups --------------------
    #path('locks-groups/', lock_group_views.locks_groups, name='locks-groups'),
    path('locks-groups-by-project/<int:project_id>/', lock_group_views.locks_groups_by_project, name='locks-groups-by-project'),
    path('locks-groups/search/', lock_group_views.lock_group_search, name='lock-group-search'),
    path('locks-groups/form/', lock_group_views.lock_group_form, name='lock-group-form'),
    path('locks-groups/save/', lock_group_views.lock_group_save, name='lock-group-save'),
    path('locks-groups/remove/', lock_group_views.lock_group_remove, name='lock-group-remove'),
    path('locks-groups/remove-by-id/', lock_group_views.lock_group_remove_by_id, name='lock-group-remove-by-id'),
    path('locks-groups/add/', lock_group_views.lock_group_add, name='lock-group-add'),

    #--------------------- Locks Cron --------------------
    path('locks-cron/<int:project_id>/', lock_cron_views.locks_cron, name='locks-cron'),
    path('locks-cron/row/', lock_cron_views.lock_row, name='lock-cron-row'),
    path('locks-cron/search/', lock_cron_views.lock_search, name='lock-cron-search'),
    path('locks-cron/set-action/', lock_cron_views.lock_set_action, name='lock-cron-set-action'),
    path('locks-cron/set-task/', lock_cron_views.lock_set_task, name='lock-cron-set-task'),
    #path('locks/form/', lock_views.lock_form, name='lock-form'),
    #path('locks/remove/', lock_views.lock_remove, name='lock-remove'),
    #path('locks/get-all-passcodes/', lock_views.lock_get_all_passcodes, name='lock-get-all-passcodes'),
    #path('locks/remove/code/', lock_views.lock_remove_code, name='lock-remove-code'),
    #path('locks/remove-all-passcodes/', lock_views.lock_remove_all_passcodes, name='lock-remove-all-passcodes'),
    #path('locks/get-all-cards/', lock_views.lock_get_all_cards, name='lock-get-all-cards'),
    #path('locks/remove/card/', lock_views.lock_remove_card, name='lock-remove-card'),
    #path('locks/remove-all-cards/', lock_views.lock_remove_all_cards, name='lock-remove-all-cards'),
    #path('locks/get-all-records/', lock_views.lock_get_all_records, name='lock-get-all-records'),

    path('locks-cron/tasks-by-project/', lock_cron_views.locks_tasks_by_project, name='locks-tasks-by-project'),
    path('locks-cron/tasks-add/', lock_cron_views.locks_tasks_add, name='locks-task-add'),
    path('locks-cron/tasks-type/', lock_cron_views.locks_tasks_type, name='locks-task-type'),
    path('locks-cron/tasks-params/', lock_cron_views.locks_tasks_params, name='locks-task-params'),
    path('locks-cron/tasks-locks/', lock_cron_views.locks_tasks_locks, name='locks-task-locks'),

    #--------------------- Boxes --------------------
    path('boxes/by-project/', box_views.boxes_by_project, name='boxes-by-project'),
    path('boxes/card/by-project/', box_views.box_card_by_project, name='box-card-by-project'),
    path('boxes/form/by-project/', box_views.box_form_by_project, name='box-form-by-project'),
    path('boxes/search/by-project/', box_views.box_search_by_project, name='box-search-by-project'),
    path('boxes/box-add-code/', box_views.box_add_code, name='box-add-code'),

    #--------------------- Sensibo devices --------------------
    #path('sensibo-device-by-project/<int:project_id>/', sensibo_views.devices_by_project, name='sensibo-device-by-project'),
    #path('sensibo-device-switch/', sensibo_views.device_switch, name='sensibo-device-switch'),
    #path('sensibo-device-set-state/', sensibo_views.device_set_state, name='sensibo-device-set-state'),
    #path('sensibo-device-save-room/', sensibo_views.device_save_room, name='sensibo-device-save-room'),
    #path('sensibo-device-by-project2/', sensibo_views.devices_by_project2, name='sensibo-device-by-project2'),
    #path('sensibo-device-switch-project/', sensibo_views.device_switch_project, name='sensibo-device-switch-project'),
    #path('sensibo-device-set-state-project/', sensibo_views.device_set_state_project, name='sensibo-device-set-state-project'),

    #--------------------- Rooms --------------------
    path('rooms/', room_views.rooms, name='rooms'),
    #path('rooms/search/', room_views.room_search, name='room-search'),
    #path('rooms/floors/', room_views.room_floors, name='room-floors'),
    path('rooms/list/', room_views.room_list, name='room-status-list'),
    path('rooms/form/', room_views.room_form, name='room-form'),
    path('rooms/remove/', room_views.room_remove, name='room-remove'),
    path('rooms/search/', room_views.rooms_search, name='rooms-search'),
    path('rooms/lock-details/', room_views.room_lock_details, name='room-lock-details'),
    path('rooms/lock-list/', room_views.room_lock_list, name='room-lock-list'),
    path('rooms/set-group/', room_views.room_set_group, name='room-set-group'),
    path('rooms/multiple/', room_views.room_multiple, name='room-multiple'),
    path('rooms/multiple-save/', room_views.room_multiple_save, name='room-multiple-save'),
    path('rooms/import-csv/', room_views.room_import_csv, name='room-import-csv'),
    path('rooms/import/', room_views.room_import, name='room-import'),
    #path('rooms/lock-add/', room_views.room_lock_add, name='room-lock-add'),
    path('rooms/lock-add-card/', room_views.room_lock_add_card, name='room-lock-add-card'),
    path('rooms/lock-remove-card/', room_views.room_lock_remove_card, name='room-lock-remove-card'),
    path('rooms/lock-add-code/', room_views.room_lock_add_code, name='room-lock-add-code'),
    path('rooms/lock-remove-code/', room_views.room_lock_remove_code, name='room-lock-remove-code'),
    path('rooms/lock-add-ekey/', room_views.room_lock_add_ekey, name='room-lock-add-ekey'),
    path('rooms/lock-remove-ekey/', room_views.room_lock_remove_ekey, name='room-lock-remove-ekey'),
    path('ekey-url/<slug:token>/', room_views.ekey_url, name='ekey-url'),

    #--------------------- Rooms by projects --------------------
    path('rooms/by-project/', room_views.rooms_by_project, name='rooms-by-project'),
    path('rooms/list/by-project/', room_views.room_list_by_project, name='room-list-by-project'),
    path('rooms/form/by-project/', room_views.room_form_by_project, name='room-form-by-project'),
    path('rooms/search/by-project/', room_views.rooms_search_by_project, name='rooms-search-by-project'),

    path('rooms2/by-project/', room_views.rooms2_by_project, name='rooms2-by-project'),
    path('rooms2/by-project/search/', room_views.rooms2_search_by_project, name='rooms2-search-by-project'),
    path('rooms2/by-project/get-card/', room_views.rooms2_get_card, name='rooms2-get-card'),
    path('rooms2/by-project/get-all-cards/', room_views.rooms2_get_all_cards, name='rooms2-get-all-cards'),

    #--------------------- KeyCard --------------------
    #path('keycards/', card_views.keycards, name='keycards'),
    path('keycards/by-project/<slug:project_uuid>/', card_views.keycards_by_project, name='keycards-by-project'),
    path('keycards/search/', card_views.keycard_search, name='keycard-search'),
    path('keycards/form/', card_views.keycard_form, name='keycard-form'),
    path('keycards/remove/', card_views.keycard_remove, name='keycard-remove'),

    path('utils/add-multiple/<slug:project_uuid>/', card_views.keycards_add_multiple, name='keycards-add-multiple'),
    path('utils/add-multiple-by-project/', card_views.keycards_add_multiple_by_project, name='keycards-add-multiple-by-project'),
    path('utils/add-multiple-by-project/<int:group>/', card_views.keycards_add_multiple_by_project, name='keycards-add-multiple-by-project'),
    path('utils/add-multiple-code-by-project/', card_views.keycode_add_multiple_by_project, name='keycode-add-multiple-by-project'),
    path('utils/add-multiple-code-by-project/<int:group>/', card_views.keycode_add_multiple_by_project, name='keycode-add-multiple-by-project'),
    path('utils/add-multiple-step1/', card_views.keycards_add_multiple_step1, name='keycards-add-multiple-step1'),
    path('utils/add-multiple-step2/', card_views.keycards_add_multiple_step2, name='keycards-add-multiple-step2'),
    path('utils/add-multiple-step3/', card_views.keycards_add_multiple_step3, name='keycards-add-multiple-step3'),
    path('utils/add-multiple-locks/', card_views.keycards_add_multiple_locks, name='keycards-add-multiple-locks'),
    path('utils/add-multiple-locks-select/', card_views.keycards_add_multiple_locks_select, name='keycards-add-multiple-locks-select'),

    path('keycards/number/', card_views.keycard_number, name='keycard-number'),
    path('keycards/number-search/', card_views.keycard_number_search, name='keycard-number-search'),
    path('keycards/number-guest-remove/', card_views.keycard_number_guest_remove, name='keycard-number-guest-remove'),
    path('keycards/number-by-project/', card_views.keycard_number_by_project, name='keycard-number-by-project'),
    path('keycards/number-search-by-project/', card_views.keycard_number_search_by_project, name='keycard-number-search-by-project'),
    path('keycards/number-guest-remove-by-project/',card_views.keycard_number_guest_remove_by_project,name='keycard-number-guest-remove-by-project'),

    #--------------------- Gateways --------------------
    path('gateways-by-project/<int:project_id>/', gateway_views.gateways_by_project, name='gateways-by-project'),
    path('gateways-by-project2/', gateway_views.gateways_by_project2, name='gateways-by-project2'),

    #--------------------- eKeys --------------------
    path('ekeys-by-project/<int:project_id>/', ekey_views.ekeys_by_project, name='ekeys-by-project'),

    #--------------------- Connector --------------------
    #path('connector/avantio/get-booking-list/', connector_views.avantio_get_booking_list, name='connector-avantio-get-booking-list'),

    #---------------------- E-Keys ---------------------
    #path('ekeys/', views.ekeys, name='ekeys'),

    #--------------------- Modules --------------------
    path('show-module/', views.show_module, name='show-module'),

    #--------------------- Utils --------------------
    path('show-utils/', views.show_utils, name='show-utils'),

    #--------------------- Logs --------------------
    path('logs/', views.logs, name='logs'),
    path('download-log/', views.download_log, name='download-log'),

    #---------------------- Tests ----------------------
    path('thanks/', views.thanks),
    path('check-error/', views.check_error),

    #---------------------- AUTO -----------------------
    path('autosave_field/', auto_views.autosave_field, name='autosave_field'),
    path('autosave_fields/', auto_views.autosave_fields, name='autosave_fields'),
    path('autoremove_obj/', auto_views.autoremove_obj, name='autoremove_obj'),
]

