cat << 'EOF'
 _________________________________________ 
/                                         \
|                                         |
| We are starting the Main Deploy         |
| Script...... Please be patient ... this |
| may take some time                      |
|                                         |
\                                         /
 ----------------------------------------- 
      \                    / \  //\
       \    |\___/|      /   \//  \\
            /0  0  \__  /    //  | \ \    
           /     /  \/_/    //   |  \  \  
           @_^_@'/   \/_   //    |   \   \ 
           //_^_/     \/_ //     |    \    \
        ( //) |        \///      |     \     \
      ( / /) _|_ /   )  //       |      \     _\
    ( // /) '/,_ _ _/  ( ; -.    |    _ _\.-~        .-~~~^-.
  (( / / )) ,-{        _      `-.|.-~-.           .~         `.
 (( // / ))  '/\      /                 ~-. _ .-~      .-~^-.  \
 (( /// ))      `.   {            }                   /      \  \
  (( / ))     .----~-.\        \-'                 .~         \  `. \^-.
             ///.----..>        \             _ -~             `.  ^-`  ^-_
               ///-._ _ _ _ _ _ _}^ - - - - ~                     ~-- ,.-~
                                                                  /.-~

EOF

echo """ 

Starting Build ... And Push

"""
set -e
echo "using docker Repo --- $1 " | docker login $1
docker rmi -f $1:$2 || true
docker build -t scanner:$2 app
docker tag scanner:$2 $1:$2
docker push $1:$2
docker rmi -f $1:$2 || true
docker rmi -f scanner:$2 || true
cat << 'EOF'


 _______________________________________ 
/                                       \
| BTW I created the docker Image for    |
\ you!!!                                /
 --------------------------------------- 
\                             .       .
 \                           / `.   .' " 
  \                  .---.  <    > <    >  .---.
   \                 |    \  \ - ~ ~ - /  /    |
         _____          ..-~             ~-..-~
        |     |   \~~~\.'                    `./~~~/
       ---------   \__/                        \__/
      .'  O    \     /               /       \  " 
     (_____,    `._.'               |         }  \/~~~/
      `----.          /       }     |        /    \__/
            `-.      |       /      |       /      `. ,~~|
                ~-.__|      /_ - ~ ^|      /- _      `..-'   
                     |     /        |     /     ~-.     `-. _  _  _
                     |_____|        |_____|         ~ - . _ _ _ _ _>




EOF



gcloud run deploy scanner \
--image=$1:$2 \
--allow-unauthenticated \
--cpu=8 \
--memory=32Gi \
--timeout=1200 \
--min-instances=1 \
--max-instances=6 \
--execution-environment=gen2 \

