window.onload=function(){
  var vote_counts = [5, 1, 69, 1, 5];
  var winners = [false, false, false, false, false];
  var badges = document.getElementsByClassName("badge");
  var i;
  var maxIndex = 0;
  for(i = 0; i < 5; i++){
      badges[i].textContent=vote_counts[i];
      if(vote_counts[i] > vote_counts[maxIndex]){
          winners = [false, false, false, false, false];
          maxIndex = i;
          winners[i] = true;
      } else if (vote_counts[i] == vote_counts[maxIndex]){
          winners[i] = true;
      }
  }

  for(i = 0; i < 5; i++){
      if(winners[i] == true){
          badges[i].classList.remove("badge-info");
          badges[i].classList.add("badge-success");
      }
  }
}
