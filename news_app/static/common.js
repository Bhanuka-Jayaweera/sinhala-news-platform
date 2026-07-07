$(".feedback-positive").click(function(){
    
    news_category = $(this).parent().parent().parent().siblings(':last').children(':first').text()
    news_id = $(this).parent().parent().siblings(':last').val()

    var csrftoken = jQuery("[name=csrfmiddlewaretoken]").val();

    $.ajax({
        type: 'POST',
        url: 'recommendation',
        beforeSend: function (xhr){
            xhr.setRequestHeader('X-CSRFToken', csrftoken);
        },
        contentType: "application/json; charset=utf-8",
        dataType: 'json',
        data: JSON.stringify({
            category: news_category,
            feedback_type: "positive",
            news_id: news_id,
            csrfmiddlewaretoken: window.CSRF_TOKEN
        }),
        success: function(data){
            console.log("Data: " + data);
        }
    });
});

$(".feedback-negative").click(function(){
    
    news_category = $(this).parent().parent().parent().siblings(':last').children(':first').text()
    news_id = $(this).parent().parent().siblings(':last').val()

    var csrftoken = jQuery("[name=csrfmiddlewaretoken]").val();

    $.ajax({
        type: 'POST',
        url: 'recommendation',
        beforeSend: function (xhr){
            xhr.setRequestHeader('X-CSRFToken', csrftoken);
        },
        contentType: "application/json; charset=utf-8",
        dataType: 'json',
        data: JSON.stringify({
            category: news_category,
            feedback_type: "negative",
            news_id: news_id,
            csrfmiddlewaretoken: window.CSRF_TOKEN
        }),
        success: function(data){
            console.log("Data: " + data);
        }
    });
});