//TODO: remove 1 extra function call to add entry per submit

//var tbodyRef = document.getElementById("myTable").getElementsByTagName('tbody')[0];
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
        var trHTML='';
        //console.log(str);
        //console.log(document.getElementById("result").innerHTML);
        document.getElementById("result").innerHTML = str.ID + ", " + str.Rating; //turn into text instead of updating the obj
        //console.log(document.getElementById("result").innerHTML); //see if it's updated
        // $.each(data, function(i, item){
        //   alert(data[i].ID);
        //   trHTML +=
        //     '<tr><td>' + item.ID +
        //     '</td><td>' +item.Rating +
        //     '</td><tr>';
        // });
        // $('#myTable tbody').append(trHTML)

      },
      error: function(data){
        console.log("Error:", data);
      }
    });
    return false;
  });

  //save in dynamodb
  $("#request").submit(function(data){ //use tag to bind JS to funcone("click",
    var API_URL = '/iris_alexa_webpage'; //send request to API gateway URL //test/iris_alexa_webpage
    //var request_method = $(this).attr("method"); //return post
    var formData = {ID:$('#Username').val()}
    data.preventDefault();
    // data.stopImmediatePropagation(); //prevent the event from bubbling up thorugh the dom
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
          var trHTML='';
          //console.log(str);
        //  console.log(document.getElementById("result").innerHTML);
        //  document.getElementById("result").innerHTML = str.ID + ", " + str.Rating; //turn into text instead of updating the obj
        //  console.log(document.getElementById("result").innerHTML);
        console.log(data)
          //https://api.jquery.com/each/
          $.each(data, function(i, item){ //iterates over the DOM elements that are part of the jQuery object
            console.log(data["body"]["Item"])
            trHTML +=
              '<tr><td>' + str.ID +
              '</td><td>' +str.Feeling +
              '</td><td>' +str.Rating +
              '</td><td>' +str.Date +
              '</td><tr>';
            return false;
          });
          $('#myTable tbody').append(trHTML)
        },
        error: function(data){
          console.log("Error:", data)
        }
    });
    return false; //avoid button being clicked all the time
  });
});
