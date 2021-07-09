//jQuery detects a page's dynamic DOM readiness for JS
$(document).ready(function(){
  var headers={'Content-Type': 'application/json'};// , 'Access-Control-Allow-Origin':'*'};
  var API_URL = '/iris_alexa_webpage'; ///test/iris_alexa_webpage

  $.ajaxSetup({
    beforeSend: function(xhr) {
    xhr.setRequestHeader("Content-Type", "application/json");
    }
  });

  $("#getdata").submit(function(){ //print to screen
    $.ajax({
      type: "GET",
      headers: headers,
      dataType: "json",
      url: API_URL,
      success: function(data){
        var str = data["body"]["Item"];
        console.log(str);
        console.log(document.getElementById("result").innerHTML);
        document.getElementById("result").innerHTML = str.id + ", " + str.password + ", " + str.amount + ", " + str.color; //turn into text instead of updating the obj
        console.log(document.getElementById("result").innerHTML); //see if it's updated
      },
      error: function(data){
        console.log("Error:", data);
      }
    });
  });

  //save in dynamodb
  $("#request").submit(function(data){ //use tag to bind JS to func
    var API_URL = '/iris_alexa_webpage'; //send request to API gateway URL //test/iris_alexa_webpage
    //var request_method = $(this).attr("method"); //return post
    var formData = {user:$('#Username').val(), pass:$('#Password').val()}
    $.ajax({
        type: "POST",
        headers: headers,
        url: API_URL,
        contentType: "application/json",
        data: JSON.stringify(formData),
        cors: true ,
        //TODO: on success, print to screen the value just posted.
        success: function(data) {
          var str = data["body"]["Item"];
          console.log(str);
          console.log(document.getElementById("result").innerHTML);
          document.getElementById("result").innerHTML = str.id + ", " + str.password + ", " + str.amount + ", " + str.color; //turn into text instead of updating the obj
          console.log(document.getElementById("result").innerHTML);
        },
        error: function(data){
          console.log("Error:", data)
        }
    });
    return false; //avoid button being clicked all the time
  });
});
