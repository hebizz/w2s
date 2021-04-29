from backend.handlers import (
    base,
    login,
    user,
    admin,
    camera,
    alerts,
    function,
    overview,
    download,
    income)


url_patterns = [
    (r"/", base.BaseHandler),
    (r"/api/v1/healthy", base.BaseHandler),

    (r"/api/v1/login", login.LoginHandler),
    (r"/api/v1/logout", login.LogoutHandler),

    # user management
    (r"/api/v1/user", user.Handler),
    (r"/api/v1/admin/user", admin.Handler),

    (r"/api/v1/overview", overview.OverviewHandler),
    (r"/api/v1/overview/location", overview.OverviewLocationHandler),

    # camera
    (r"/api/v1/camera", camera.CameraHandler),
    (r"/api/v1/camera/flavour", camera.FlavourHandler),
    (r"/api/v1/devices/summary", camera.CameraSummaryHandler),
    (r"/api/v1/devices/image", camera.CameraHistoryHandler),
    (r"/api/v1/devices/camera", camera.CameraManagementHandler),

    # alert
    (r"/api/v1/alerts", alerts.AlertsHandler),
    (r"/api/v1/alerts/delete", alerts.AlertsDeleteHandler),
    (r"/api/v1/alerts/refresh", alerts.RefreshHandler),
    (r"/api/v1/alerts/summary", alerts.AlertsSummaryHandler),
    (r"/api/v1/alerts/summary/status", alerts.AlertsSummaryStatusHandler),
    (r"/api/v1/alerts/summary/category", alerts.AlertsSummaryCategoryHandler),

    # function
    (r"/api/v1/function", function.FunctionHandler),
    (r"/api/v1/function/camera", function.CameraSetHandler),

    # report
    (r"/api/v1/alerts/excel", download.DownloadHandler),

    # import alert
    # (r"/api/v2/income", income.IncomeHandler),
]
