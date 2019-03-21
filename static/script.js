var candidateNames = [
    "A feeling",
    "More than a feeling",
    "A color",
    "Y'know, just, life",
    "Eiffel 65",
]

window.onload=function(){
  document.getElementById("Op1").addEventListener("click", op1);
  document.getElementById("Op2").addEventListener("click", op2);
  document.getElementById("Op3").addEventListener("click", op3);
  document.getElementById("Op4").addEventListener("click", op4);
  document.getElementById("Op5").addEventListener("click", op5);
  document.getElementById("vote-btn").addEventListener("click", submitVote);
  var candidate_list = document.getElementsByClassName("candidate");
  var i;
  for(i = 0; i < candidate_list.length; i++){
    candidate_list[i].addEventListener("mousedown", clearCandidate);
  }
}

function getFileInfo(){
    // Code taken from https://stackoverflow.com/questions/857618/javascript-how-to-extract-filename-from-a-file-input-control
    var fullPath = document.getElementById("vote-key-file").value;
    if (fullPath) {
        var startIndex = (fullPath.indexOf('\\') >= 0 ? fullPath.lastIndexOf('\\') : fullPath.lastIndexOf('/'));
        var filename = fullPath.substring(startIndex);
        if (filename.indexOf('\\') === 0 || filename.indexOf('/') === 0) {
            filename = filename.substring(1);
        }
        var textlabel = document.getElementById("file-label");
        textlabel.textContent = filename;
    }
}

function clearCandidate(){
  console.log("Candidates Cleared");
  var active_element = document.getElementsByClassName("active")[0];
  if(active_element){
    active_element.classList.remove("active");
  }
}

function op1(){document.getElementById("Op1").classList.add("active");}
function op2(){document.getElementById("Op2").classList.add("active");}
function op3(){document.getElementById("Op3").classList.add("active");}
function op4(){document.getElementById("Op4").classList.add("active");}
function op5(){document.getElementById("Op5").classList.add("active");}

function submitVote(){
  var id = document.getElementById("voting-id").value;
  var key = document.getElementById("vote-key-file").value;
  var candidate_list = document.getElementsByClassName("candidate");
  var i;
  var voteID = 0;
  for(i = 0; i < 5; i++){
      if(candidate_list[i].classList.contains("active")){
          voteID = i;
      }
  }
  console.log("ID: ", id);
  console.log("Key: ", key);
  console.log("Candidate: ", candidateNames[voteID]);
  var VOTE_URL = window.location.href + "vote";
  var r = new FileReader();
  r.readAsText(document.getElementById("vote-key-file").files[0], "UTF-8");
  r.onload = function(){
      $.post("vote/", {id: id, key: r.result, candidate: candidateNames[voteID]},
       function(data, status){
           redirect(data);
       }, "json");
  };
}

function redirect(data){
    console.log("SERVER RETURNED: ", data);
    if(data.status == "success"){
        window.location.assign(window.location.href + "results/");
    } else {
        alert("Vote invalid. Either the listed ID / Key is not correct, or you've already voted.");
    }
}
