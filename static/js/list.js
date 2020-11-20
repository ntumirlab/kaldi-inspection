Number.prototype.round = function (places) {
  return +(Math.round(this + "e+" + places) + "e-" + places);
}

// update by adler 20.10.2020
// sort data by wer order by desc.
function getSortedObjectKeys(o) {
  let arr = [];
  for (let key in o) {
    arr.push({ 'utt': key, 'wer': o[key].wer.round(4) });
  }
  // If two elements have different number, then the one who has larger number wins
  return arr.sort(function (a, b) { return b.wer - a.wer; }).map(function (o) { return o.utt; });
}

$('#list-fetch-form').on('submit', function (event) {
  event.preventDefault();
  $("#listInfo").html("");
  $("#listWrapper").html("Loading...");
  let input_form = $('#list-fetch-form') ; 
  let decode_options = input_form.find("select[name=decode-options]") ;
  let criterion = input_form.find("select[name=criterion]").val() ;
  let quantity = input_form.find("select[name=quantity]").val() ;

  if (decode_options) {
    let decode_id = decode_options.val();
    $.ajax({
      url: '/list/fetch',
      method: "GET",
      data: {
        decode_id: decode_id,
        criterion: criterion
      },
    }).done(data => {
      if (data.success) {
        if (data.content['error'] != null){
            $("#listInfo").html(data.content['error']);
            $("#listWrapper").html("");
            return false;
        }
        listInfoHtml = "<h3 id=\"decode_id\" name=\"" + decode_id + "\"> result of " + decode_id + " (overall WER: " + data.content.wer + "%)</h3>";
        if (data.content.criterion_file != "") {
            listInfoHtml += "<h5><a href=" + data.content.criterion_file + " target=\"_blank\">download result file</a></h5>";
        }
        $("#listInfo").html(listInfoHtml);
        $("#listWrapper").html("");
        listResult( data , quantity );
      }
      else {
        $("#listWrapper").html("<div> <p> 發生錯誤 </p> </div>");
      }
    });
    return false;
  }
});

// update by adler 20.10.2020
// check csid and give difference class , return the HTML code of ops/ref/hyp
function csidClasses( uttData ){
  let opsHTML = "" , refHTML = "" , hypHTML = "" ;
  let csidClass = "" ;
  for( let i = 0 ; i < uttData.op.length ; i ++ ){
    let ops = uttData.op[i] ;
    let ref = uttData.ref[i] ;
    let hyp = uttData.hyp[i] ;
    switch( ops.toLowerCase() ){
      case 'c' :
        csidClass = "correct" ;
        break ;
      case 's' :
        csidClass = "substitution" ;
        break ;
      case 'i' :
        csidClass = "insert" ;
        break;
      case 'd' :
        csidClass = "delete" ;
        break ;
      default :
        csidClass = "" ;
        break ;
    }
    opsHTML += "<span class=\"" + csidClass + "\">" + ops + "</span> " ;
    refHTML += "<span class=\"" + csidClass + "\">" + ref + "</span> " ;
    hypHTML += "<span class=\"" + csidClass + "\">" + hyp + "</span> " ;
  }
  return [opsHTML, refHTML, hypHTML] ;
}


// update by adler 29.10.2020
// list all uttrence ctm result in div#listWrapper
function listResult( data , quantity ) {
  let utts = data.content.utts ;
  keys = getSortedObjectKeys(utts);
  
  // selected elements by display quantity
  if( quantity != 'all' ){
    quantity = parseInt(quantity) ;
    keys = keys.slice(0, quantity) ;
  }

  let listWrapperHTML = "" ;
  keys.forEach(key => {
    // set all display row
    let orhHTMLList = csidClasses( data.content.utts[key] ) ;  // get ops/ref/hyp HTML with csid classes
    let opsHTML = orhHTMLList[0] , refHTML = orhHTMLList[1] , hypHTML = orhHTMLList[2] ;

    keyHTML = "<h5><a href=\"" + data.content.utts[key].ctm_link + "\" target=\"_blank\"> " + key + " </a></h5>" ;
    keyHTML += "<h5>csid: </h5> <p>" + data.content.utts[key].csid + "</p>" ;
    keyHTML += "<h5>ops: </h5> <p id=\"ops\">" + opsHTML + "</p>" ;
    keyHTML += "<h5>wer: </h5> <p>" + data.content.utts[key].wer.round(4) + "</p>" ;
    keyHTML += "<h5>ref: </h5> <p id=\"ref\">" + refHTML + "</p>" ;
    keyHTML += "<h5>hyp: </h5> <p id=\"hyp\">" + hypHTML + "</p>" ;
    keyHTML += "<h5>audio: </h5> <div class=\"icono-play audio\" onclick=\"playAudio(this, \'" + key + "\');\"></div>" ;

    listWrapperHTML += "<div class=list-item id=\"" + key + "\">" + keyHTML + "</div>" ;
  });
  $("#listWrapper").html( listWrapperHTML ) ;
}

// create by adler 29.10.2020
// play uttrence audio 
function playAudio( click_btn , utt_id ) {
  // disable click event when audio playing
  click_btn.style.pointerEvents = "none";
  
  // get wav path to play audio
  let decode_id = $("#listInfo").find("h3#decode_id").attr("name") ;
  $.ajax({
    url: '/list/audio',
    method: "GET",
    data: {
      decode_id: decode_id,
      uttid: utt_id
    },
  }).done(data => {
    if (data.success) {
      let content = data['content'];
      let wavFile = content['wav'];
      let segments = content['segments'];
      
      // create a audio object and play
      let audio = new Audio(wavFile);
      if( segments ){
        // play with segments
        let startTime = segments[0];
        let endTime = segments[1];
        let duration = endTime - startTime;
        
        audio.currentTime = startTime ;
        audio.play();
        // stop & enable click event after duration time out
        setTimeout(function(){ 
          audio.pause();
          click_btn.style.pointerEvents = "";
        }, duration*1000);
      } else {
        // play full
        audio.play();
        // enable click event after play
        audio.addEventListener("pause", function() {
            click_btn.style.pointerEvents = "";
          }
        );
      }
    }
    else {
      // print error message
      click_btn.setAttribute("class","");
      click_btn.innerHTML = "<p>" + data['message'] + "</p>"
    }
  });
  
}
