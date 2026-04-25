from django.shortcuts import render
from django.template import RequestContext
from django.contrib import messages
from django.http import HttpResponse
from django.conf import settings
import os
import pymysql
from django.core.files.storage import FileSystemStorage
from pyspark import sql, SparkConf, SparkContext#loading spark classes
import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score
from sklearn.metrics import precision_score
from sklearn.metrics import recall_score
from sklearn.metrics import accuracy_score
import io
import base64
import matplotlib.pyplot as plt
from sklearn.tree import DecisionTreeClassifier
from sklearn import svm
import seaborn as sns
from sklearn.metrics import confusion_matrix

global username, X, Y, dataset
global uname, rf_model, scaler, label_encoder
global X_train, X_test, y_train, y_test, labels
global accuracy, precision, recall, fscore

# ===== ML Global Variables Initialization =====
rf_model = None
scaler = None
label_encoder = []
labels = []

X = None
Y = None
dataset = None

X_train = None
X_test = None
y_train = None
y_test = None

accuracy = []
precision = []
recall = []
fscore = []

#function to initialize spark session
spark_session = sql.SparkSession.builder.appName("HDFS").getOrCreate()
spark_context = SparkContext.getOrCreate(SparkConf().setAppName("HDFS"))
logs = spark_context.setLogLevel("ERROR")
print("Spark Session Initialized with Hadoop HDFS")

def PredictParam(request):
    if request.method == 'GET':
        return render(request, 'PredictParam.html', {})

def PredictFile(request):
    if request.method == 'GET':
        return render(request, 'PredictFile.html', {})

def PredictParamAction(request):
    global username
    if request.method == 'POST':
        global rf_model, scaler, label_encoder, labels
        gender = request.POST.get('t1', False)
        heart = request.POST.get('t2', False)
        activity = request.POST.get('t3', False)
        sleep = request.POST.get('t4', False)
        mood = request.POST.get('t5', False)
        testData = pd.DataFrame([[gender.strip(), float(heart.strip()), activity.strip(), sleep.strip(), mood.strip()]], columns=["Gender", "Heart_Rate", "Physical_Activity", "Sleep_Quality", "Mood"])
        temp = testData.values
        for j in range(len(label_encoder)-1):
            le = label_encoder[j]
            testData[le[0]] = pd.Series(le[1].transform(testData[le[0]].astype(str)))#encode all str columns to numeric
        testData.fillna(0, inplace = True)
        testData = testData.values
        testData = scaler.transform(testData)
        predict = rf_model.predict(testData)
        columns = ["Gender", "Heart_Rate", "Physical_Activity", "Sleep_Quality", "Mood"]
        output='<table border=1 align=center width=100%><tr>'
        for i in range(len(columns)):
            output += '<th><font size="3" color="black">'+columns[i]+'</th>'
        output += '<th><font size="3" color="black">Predicted Health Status</th>'    
        output += '</tr>'
        for i in range(len(temp)):
            output += '<tr>'
            for j in range(len(temp[i])):
                output += '<td><font size="3" color="black">'+str(temp[i,j])+'</td>'
            status = labels[predict[i]]
            if status == 'Low':
                output += '<td><font size="3" color="green">Good Health Predicted</td>'
            if status == 'Moderate':
                output += '<td><font size="3" color="orange">Moderate Health Predicted</td>'
            if status == 'High':
                output += '<td><font size="3" color="orange">Low Health Predicted</td>'
            output += '</tr>'
        output+= "</table></br>"
        prob = rf_model.predict_proba(testData)
        prob = prob.ravel()
        print(prob)
        height = prob
        bars = labels
        y_pos = np.arange(len(bars))
        plt.figure(figsize = (4, 3)) 
        plt.bar(y_pos, height)
        plt.xticks(y_pos, bars)
        plt.xlabel("Health Status")
        plt.ylabel("Probability")
        plt.title("Health Predicted Probability Graph")
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        img_b64 = base64.b64encode(buf.getvalue()).decode()
        plt.clf()
        plt.cla()
        context= {'data':output, 'img': img_b64}
        return render(request, 'UserScreen.html', context)
        context= {'data':output}
        return render(request, 'UserScreen.html', context)
        
def PredictFileAction(request):
    if request.method == 'POST':
        global rf_model, scaler, label_encoder, labels
        myfile = request.FILES['t1'].read()
        fname = request.FILES['t1'].name
        if os.path.exists("HealthApp/static/"+fname):
            os.remove("HealthApp/static/"+fname)
        with open("HealthApp/static/"+fname, "wb") as file:
            file.write(myfile)
        file.close()
        testData = pd.read_csv("HealthApp/static/"+fname)
        testData = testData[["Gender", "Heart_Rate", "Physical_Activity", "Sleep_Quality", "Mood"]]
        temp = testData.values
        for j in range(len(label_encoder)-1):
            le = label_encoder[j]
            testData[le[0]] = pd.Series(le[1].transform(testData[le[0]].astype(str)))#encode all str columns to numeric
        testData.fillna(0, inplace = True)
        testData = testData.values
        testData = scaler.transform(testData)
        predict = rf_model.predict(testData)
        columns = ["Gender", "Heart_Rate", "Physical_Activity", "Sleep_Quality", "Mood"]
        output='<table border=1 align=center width=100%><tr>'
        for i in range(len(columns)):
            output += '<th><font size="3" color="black">'+columns[i]+'</th>'
        output += '<th><font size="3" color="black">Predicted Health Status</th>'    
        output += '</tr>'
        for i in range(len(temp)):
            output += '<tr>'
            for j in range(len(temp[i])):
                output += '<td><font size="3" color="black">'+str(temp[i,j])+'</td>'
            status = labels[predict[i]]
            if status == 'Low':
                output += '<td><font size="3" color="green">Good Health Predicted</td>'
            if status == 'Moderate':
                output += '<td><font size="3" color="orange">Moderate Health Predicted</td>'
            if status == 'High':
                output += '<td><font size="3" color="red">Low Health Predicted</td>'
            output += '</tr>'
        output+= "</table></br></br></br></br>"
        context= {'data':output}
        return render(request, 'UserScreen.html', context)
'''def PredictFileAction(request):
    if request.method == 'POST':

        global rf_model, scaler, label_encoder, labels

        # 🔹 Ensure model is trained
        if rf_model is None or scaler is None or len(label_encoder) == 0:
            return render(request,'UserScreen.html',
                          {'data':'Please ask Admin to Load Dataset and Train ML Model first!'})

        myfile = request.FILES['t1'].read()
        fname = request.FILES['t1'].name

        path = "HealthApp/static/"+fname

        if os.path.exists(path):
            os.remove(path)

        with open(path,"wb") as file:
            file.write(myfile)

        testData = pd.read_csv(path)

        testData = testData[["Gender","Heart_Rate","Physical_Activity","Sleep_Quality","Mood"]]

        temp = testData.values

        # Encode categorical columns
        for j in range(len(label_encoder)):
            le = label_encoder[j]
            testData[le[0]] = pd.Series(le[1].transform(testData[le[0]].astype(str)))

        testData.fillna(0,inplace=True)

        testData = scaler.transform(testData.values)

        predict = rf_model.predict(testData)

        columns = ["Gender","Heart_Rate","Physical_Activity","Sleep_Quality","Mood"]

        output='<table border=1 align=center width=100%><tr>'

        for col in columns:
            output += '<th>'+col+'</th>'

        output += '<th>Predicted Health Status</th></tr>'

        for i in range(len(temp)):

            output += '<tr>'

            for j in range(len(temp[i])):
                output += '<td>'+str(temp[i][j])+'</td>'

            status = labels[predict[i]]

            if status == 'Low':
                output += '<td style="color:green">Good Health Predicted</td>'

            elif status == 'Moderate':
                output += '<td style="color:orange">Moderate Health Predicted</td>'

            else:
                output += '<td style="color:red">Low Health Predicted</td>'

            output += '</tr>'

        output+="</table><br><br>"

        context={'data':output}

        return render(request,'UserScreen.html',context)'''       

def LoadDatasetAction(request):
    if request.method == 'POST':
        global dataset, labels
        myfile = request.FILES['t1'].read()
        fname = request.FILES['t1'].name
        if os.path.exists("HealthApp/static/"+fname):
            os.remove("HealthApp/static/"+fname)
        with open("HealthApp/static/"+fname, "wb") as file:
            file.write(myfile)
        file.close()
        dataset = spark_session.read.csv("HealthApp/static/"+fname, inferSchema=True, header=True)
        dataset = dataset.toPandas()
        dataset = dataset[["Gender", "Heart_Rate", "Physical_Activity", "Sleep_Quality", "Mood", "Health_Risk_Level"]]
        columns = dataset.columns
        labels = np.unique(dataset['Health_Risk_Level'])
        labels = labels.ravel()
        data = dataset.values
        output='<table border=1 align=center width=100%><tr>'
        for i in range(len(columns)):
            output += '<th><font size="3" color="black">'+columns[i]+'</th>'
        output += '</tr>'
        for i in range(len(data)):
            output += '<tr>'
            for j in range(len(data[i])):
                output += '<td><font size="3" color="black">'+str(data[i,j])+'</td>'
            output += '</tr>'
        output+= "</table></br></br></br></br>"
        context= {'data':output}
        return render(request, 'AdminScreen.html', context)

def calculateMetrics(algorithm, y_test, predict):
    global accuracy, precision, recall, fscore
    a = accuracy_score(y_test,predict)*100
    p = precision_score(y_test, predict,average='macro') * 100
    r = recall_score(y_test, predict,average='macro') * 100
    f = f1_score(y_test, predict,average='macro') * 100
    accuracy.append(round(a, 3))
    precision.append(round(p, 3))
    recall.append(round(r, 3))
    fscore.append(round(f, 3))          

def trainAlgorithms(X_train, X_test, y_train, y_test):
    global rf_model, labels
    rf_model = RandomForestClassifier()
    rf_model.fit(X_train, y_train)
    predict = rf_model.predict(X_test)
    calculateMetrics("Random Forest", y_test, predict)
    conf_matrix = confusion_matrix(y_test, predict)

    svm_cls = svm.SVC()
    svm_cls.fit(X_train, y_train)
    predict = svm_cls.predict(X_test)
    calculateMetrics("SVM", y_test, predict)

    dt_cls = DecisionTreeClassifier()
    dt_cls.fit(X_train, y_train)
    predict = dt_cls.predict(X_test)
    calculateMetrics("Decision Tree", y_test, predict)
    output='<table border=1 align=center width=100%><tr><th><font size="" color="black">Algorithm Name</th><th><font size="" color="black">Accuracy</th>'
    output += '<th><font size="" color="black">Precision</th><th><font size="" color="black">Recall</th><th><font size="" color="black">FSCORE</th>'
    output+='</tr>'
    algorithms = ['Random Forest', 'SVM', 'Decision Tree']
    for i in range(len(algorithms)):
        output += '<td><font size="" color="black">'+algorithms[i]+'</td><td><font size="" color="black">'+str(accuracy[i])+'</td><td><font size="" color="black">'+str(precision[i])+'</td>'
        output += '<td><font size="" color="black">'+str(recall[i])+'</td><td><font size="" color="black">'+str(fscore[i])+'</td></tr>'
    output+= "</table></br>"
    df = pd.DataFrame([['Random Forest','Accuracy',accuracy[0]],['Random Forest','Precision',precision[0]],['Random Forest','Recall',recall[0]],['Random Forest','FSCORE',fscore[0]],
                       ['SVM','Accuracy',accuracy[1]],['SVM','Precision',precision[1]],['SVM','Recall',recall[1]],['SVM','FSCORE',fscore[1]],
                       ['Decision Tree','Accuracy',accuracy[2]],['Decision Tree','Precision',precision[2]],['Decision Tree','Recall',recall[2]],['Decision Tree','FSCORE',fscore[2]],
                     ],columns=['Parameters','Algorithms','Value'])
    figure, axis = plt.subplots(nrows=1, ncols=2,figsize=(10, 3))#display original and predicted segmented image
    axis[0].set_title("Confusion Matrix Prediction Graph")
    axis[1].set_title("All Algorithms Performance Graph")
    ax = sns.heatmap(conf_matrix, xticklabels = labels, yticklabels = labels, annot = True, cmap="viridis" ,fmt ="g", ax=axis[0]);
    ax.set_ylim([0,len(labels)])    
    df.pivot("Parameters", "Algorithms", "Value").plot(ax=axis[1], kind='bar')
    plt.title("All Algorithms Performance Graph")
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    img_b64 = base64.b64encode(buf.getvalue()).decode()
    plt.clf()
    plt.cla()
    return output, img_b64


def TrainML(request):
    if request.method == 'GET':
        global uname, rf_model, scaler, label_encoder, X, Y, dataset
        global X_train, X_test, y_train, y_test, labels
        global accuracy, precision, recall, fscore
        accuracy = []
        precision = []
        recall = [] 
        fscore = []
        label_encoder = []
        columns = dataset.columns
        types = dataset.dtypes.values
        for j in range(len(types)):
            name = types[j]
            if name == 'object': #finding column with object type
                le = LabelEncoder()
                dataset[columns[j]] = pd.Series(le.fit_transform(dataset[columns[j]].astype(str)))#encode all str columns to numeric
                label_encoder.append([columns[j], le])
        dataset.fillna(0, inplace = True)
        Y = dataset['Health_Risk_Level'].ravel()
        dataset.drop(['Health_Risk_Level'], axis = 1,inplace=True)
        X = dataset.values
        indices = np.arange(X.shape[0])
        np.random.shuffle(indices)
        X = X[indices]
        Y = Y[indices]
        scaler = StandardScaler()
        X = scaler.fit_transform(X)
        X_train, X_test, y_train, y_test = train_test_split(X, Y, test_size=0.2)
        X_train, X_test1, y_train, y_test1 = train_test_split(X, Y, test_size=0.1)
        output, img_b64 = trainAlgorithms(X_train, X_test, y_train, y_test)
        context= {'data':output, 'img': img_b64}
        return render(request, 'AdminScreen.html', context)

def LoadDataset(request):
    if request.method == 'GET':
        return render(request, 'LoadDataset.html', {})

def AdminLoginAction(request):
    global username
    if request.method == 'POST':
        global username
        username = request.POST.get('t1', False)
        password = request.POST.get('t2', False)
        if username == 'admin' and password == 'admin':
            context= {'data':'Welcome '+username}
            return render(request, "AdminScreen.html", context)
        else:
            context= {'data':'Invalid username'}
            return render(request, 'AdminLogin.html', context)

def RegisterAction(request):
    if request.method == 'POST':
        global username
        username = request.POST.get('t1', False)
        password = request.POST.get('t2', False)
        contact = request.POST.get('t3', False)
        email = request.POST.get('t4', False)
        address = request.POST.get('t5', False)
               
        output = "none"
        con = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = '', database = 'studenthealth',charset='utf8')
        with con:
            cur = con.cursor()
            cur.execute("select username FROM register")
            rows = cur.fetchall()
            for row in rows:
                if row[0] == username:
                    output = username+" Username already exists"
                    break                
        if output == "none":
            db_connection = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = '', database = 'studenthealth',charset='utf8')
            db_cursor = db_connection.cursor()
            student_sql_query = "INSERT INTO register VALUES('"+username+"','"+password+"','"+contact+"','"+email+"','"+address+"')"
            db_cursor.execute(student_sql_query)
            db_connection.commit()
            print(db_cursor.rowcount, "Record Inserted")
            if db_cursor.rowcount == 1:
                output = "Signup process completed. Login to perform Health Monitoring activities"
        context= {'data':output}
        return render(request, 'Register.html', context)
        

def UserLoginAction(request):
    global username
    if request.method == 'POST':
        global username
        status = "none"
        users = request.POST.get('t1', False)
        password = request.POST.get('t2', False)
        con = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = '', database = 'studenthealth',charset='utf8')
        with con:
            cur = con.cursor()
            cur.execute("select username,password FROM register")
            rows = cur.fetchall()
            for row in rows:
                if row[0] == users and row[1] == password:
                    username = users
                    status = "success"
                    break
        if status == 'success':
            context= {'data':'Welcome '+username}
            return render(request, "UserScreen.html", context)
        else:
            context= {'data':'Invalid username'}
            return render(request, 'UserLogin.html', context)

def Register(request):
    if request.method == 'GET':
        return render(request, 'Register.html', {})

def UserLogin(request):
    if request.method == 'GET':
       return render(request, 'UserLogin.html', {})

def AdminLogin(request):
    if request.method == 'GET':
       return render(request, 'AdminLogin.html', {})    

def index(request):
    if request.method == 'GET':
       return render(request, 'index.html', {})

