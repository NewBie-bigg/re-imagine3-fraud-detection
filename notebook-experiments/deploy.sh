echo "Cleaning existing app folders and repos...."
rm -rf app
mkdir app
rm -rf re-imagine3-fraud-detection
echo """


===============  DONE ===================


"""

git clone https://NewBie-bigg:Re-imagine%40123github.com/NewBie-bigg/re-imagine3-fraud-detection.git


gcloud config set run/region us-central1
echo "======== location set to us-central-1 ============"
echo """ 

                copying necessary files ... ... ...

"""
cp re-imagine3-fraud-detection/app-resume-to-id-matcher/* app
cp app/deploy-app.sh ./
echo """

                Removing Unnecessary Files

"""
rm -rf re-imagine3-fraud-detection
sh deploy-app.sh $1 $2
rm deploy-app.sh 
rm -rf app
echo """ 

            DONE

"""