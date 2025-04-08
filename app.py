# Required imports
from flask import Flask, render_template, request, redirect, url_for, jsonify,session
from werkzeug.utils import secure_filename
import pickle
import pandas as pd
import re
import numpy as np
import psycopg2
import io
import secrets
import hashlib
from docx import Document
from PyPDF2 import PdfReader
import requests
from bs4 import BeautifulSoup
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)



app = Flask(__name__)
app.secret_key = "secret key here"

# Database connection parameters
DB_NAME = 'database name here'
DB_USER = 'database user'
DB_PASSWORD = 'your password'
DB_HOST = 'Host name here'
DB_PORT = 'port here'

# Function to establish database connection
def connect_db():
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    return conn

# Registration page
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        unique_id = request.form['unique_id']
        phone_number = request.form['phone_number']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        address = request.form['address']

        if password != confirm_password:
            return "Passwords do not match. Please try again."

        # Connect to the database
        conn = connect_db()
        cur = conn.cursor()

        # Check if the unique ID already exists
        cur.execute("SELECT * FROM patients WHERE unique_id = %s", (unique_id,))
        if cur.fetchone():
            return "This unique ID is already registered. Please choose another one."

        # Insert new patient into the database
        cur.execute("INSERT INTO patients (name, email, unique_id, phone_number, password, address) VALUES (%s, %s, %s, %s, %s, %s)",
                    (name, email, unique_id, phone_number, password, address))
        conn.commit()
        conn.close()
        
        # Send registration confirmation email
        return redirect(url_for('login'))
    return render_template('Signup.html')


# Login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        unique_id = request.form['unique_id']
        password = request.form['password']

        # Connect to the database
        conn = connect_db()
        cur = conn.cursor()

        # Check if the unique ID and password match
        cur.execute("SELECT * FROM patients WHERE unique_id = %s AND password = %s", (unique_id, password))
        patient = cur.fetchone()
        conn.close()
        if patient:
            # Store patient's name in session
            session["loggedin"] = True
            session["unique_id"] = unique_id
            return redirect(url_for('home'))
        else:
            error = "Invalid unique ID or password. Please try again."
            return render_template('login.html', error=error)

    return render_template('login.html')


# Function to connect to PostgreSQL database
conn = psycopg2.connect(
    host="localhost",
    database="jobcatch_db",
    user='postgres',
    password='Nikhil@930'
)
cursor = conn.cursor()

# Create a table to store resume data if it does not exist already
cursor.execute("""
    CREATE TABLE IF NOT EXISTS resumes (
    id SERIAL PRIMARY KEY,
    filename TEXT NOT NULL,
    resume_text TEXT NOT NULL
    )
""")

# Commit the changes to the database
conn.commit()

# Load the model
with open('model.pkl', 'rb') as f:
    vectorizer = pickle.load(f)
    knn_model = pickle.load(f)

# Sample data for user authentication (replace with your actual data storage)
registers = {'user1': 'password1', 'user2': 'password2'}

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/resume')
def resume_generator():
        return render_template('resume.html')


@app.route('/index')
def dashboard():
    # Add code here to render the dashboard or redirect to a different page
    return render_template('index.html')

@app.route('/contact')
def contactus():
    return render_template("contact.html")

job_code_dic = {0: "Advocate", 1: "Arts", 2: "Automation Testing", 3: "Blockchain", 4: "Business Analyst",
                5: "Civil Engineer", 6: "Data Science", 7: "Database", 8: "DevOps Engineer", 9: "DotNet Developer",
                10: "ETL Developer", 11: "Electrical Engineering", 12: "HR", 13: "Hadoop",
                14: "Health and fitness", 15: "Java Developer", 16: "Mechanical Engineer",
                17: "Network Security Engineer", 18: "Operations Manager", 19: "PMO", 20: "Python Developer",
                21: "SAP Developer", 22: "Sales", 23: "Testing", 24: "Web Designing"}

job_code = {'Advocate': 'advocate', 'Arts': 'arts', 'Automation Testing': 'automation-testing', 'Blockchain': 'blockchain', 'Business Analyst': 'business-analyst', 'Civil Engineer': 'civil-engineer', 'Data Science': 'data-science', 'Database': 'database', 'DevOps Engineer': 'devops-engineer', 'DotNet Developer': 'dotnet-developer', 'ETL Developer': 'etl-developer', 'Electrical Engineering': 'electrical-engineering', 'HR': 'hr', 'Hadoop': 'hadoop', 'Health and fitness': 'health-and-fitness', 'Java Developer': 'java-developer', 'Mechanical Engineer': 'mechanical-engineer', 'Network Security Engineer': 'network-security-engineer', 'Operations Manager': 'operations-manager', 'PMO': 'pmo', 'Python Developer': 'python-developer', 'SAP Developer': 'sap-developer', 'Sales': 'sales', 'Testing': 'testing', 'Web Designing': 'web-designing'}

def cleanResume(resumeText):
    resumeText = re.sub(r'http\S+\s*', ' ', resumeText)
    resumeText = re.sub(r'RT|cc', ' ', resumeText)
    resumeText = re.sub(r'#\S+', '', resumeText)
    resumeText = re.sub(r'@\S+', '  ', resumeText)
    resumeText = re.sub(r'[%s]' % re.escape(r"""!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~"""), ' ', resumeText)
    resumeText = re.sub(r'[^\x00-\x7f]', r' ', resumeText)
    resumeText = re.sub(r'\s+', ' ', resumeText)
    return resumeText

def predict(text):
    cleaned_text = cleanResume(text)
    pWordFeatures = vectorizer.transform([cleaned_text])
    pre_prediction = knn_model.predict(pWordFeatures)
    return job_code_dic[pre_prediction[0]]


def extract_text_from_pdf(file):
    pdf_reader = PdfReader(io.BytesIO(file.read()))
    num_pages = len(pdf_reader.pages)
    text = ''
    for page_num in range(num_pages):
        page = pdf_reader.pages[page_num]
        page_text = page.extract_text()
        if page_text:
            text += page_text.strip().replace('\x00', '') + '\n'
    return text


def extract_text_from_docx(file_data):
    doc = Document(io.BytesIO(file_data))
    text = ''
    for paragraph in doc.paragraphs:
        text += paragraph.text + '\n'
    return text

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
}

@app.route('/submit', methods=['POST'])
def upload():
    if request.method == 'POST' and 'file' in request.files:
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No file selected'})

        filename = secure_filename(file.filename)
        if filename.lower().endswith('.pdf'):
            text = extract_text_from_pdf(file)
        elif filename.lower().endswith('.docx'):
            text = extract_text_from_docx(file.read())
        else:
            return render_template('index.html', message='Unsupported file format')

        cur = conn.cursor()
        cur.execute("INSERT INTO resumes (filename, resume_text) VALUES (%s, %s)", (filename, text))
        conn.commit()
        cur.close()

        try:
            job_prediction = predict(text)
            jobcode = job_code[job_prediction]

            # Glassdoor scraping (without API)
            url = f"https://www.glassdoor.co.in/Job/india-{jobcode}-jobs-SRCH_IL.0,5_IN115_KO6,19.htm"
            response = requests.get(url, headers=headers, timeout=10)
            print("response :",response)
            soup = BeautifulSoup(response.content, "html.parser")

            ul_tag = soup.find("ul", class_="JobsList_jobsList__lqjTr")
            job_list = []

            if ul_tag:
                li_tags = ul_tag.find_all("li", class_="JobsList_jobListItem__wjTHv")
                for li in li_tags:
                    try:
                        job_dic = {}

                        company_name_elem = li.find("span", class_="EmployerProfile_compactEmployerName__LE242")
                        job_title_elem = li.find("a", class_="JobCard_jobTitle___7I6y")
                        salary_elem = li.find("div", class_="JobCard_salaryEstimate__arV5J")
                        location_elem = li.find("div", class_="JobCard_location__rCz3x")
                        posted_time_elem = li.find("div", class_="JobCard_listingAge__Ny_nG")

                        job_dic["Job_Title"] = job_title_elem.text.strip() if job_title_elem else None
                        job_dic["Company_Name"] = company_name_elem.text.strip() if company_name_elem else None
                        job_dic["Location"] = location_elem.text.strip() if location_elem else "Not available"
                        job_dic["Post_Time"] = posted_time_elem.text.strip() if posted_time_elem else "Not available"
                        job_dic["Salary"] = salary_elem.text.strip() if salary_elem else "Not available"
                        job_dic["link"] = "https://www.glassdoor.co.in" + job_title_elem['href'] if job_title_elem else "Not available"

                        if job_dic["Company_Name"] and job_dic["Job_Title"]:
                            job_list.append(job_dic)
                    except Exception:
                        continue

            return render_template('index.html', prediction=job_prediction, job_dic=job_list, message='Resume Uploaded Successfully')

        except Exception as e:
            return render_template('index.html', message=f"Error: {str(e)}")

    return render_template('index.html', message='Invalid request')

# Sample interview questions data
interview_questions ={
    "Web_D": [
        {
    "question": "1. What is the difference between client-side and server-side programming?",
    "answer": "Client-side programming involves writing code that runs on the user's browser and is responsible for user interface interactions, while server-side programming deals with code executed on a web server. This code typically processes requests, communicates with databases, and generates dynamic content for websites."
    },
    {
    "question": "2. What is the use of HTTP cookies?",
    "answer": "HTTP cookies are small pieces of data sent from a website and stored in the user's browser. They're used to maintain user-specific information, such as login session identifiers, user preferences, and tracking user activity."
    },
    {
    "question": "3. Explain the concept of responsive web design",
    "answer": "Responsive web design is a method of designing websites to provide a consistent user experience across a variety of devices and screen sizes. This approach involves using flexible layouts, fluid grids, and CSS media queries to adapt the layout and appearance of a website based on the user's device and screen resolution."
    },
    {
    "question": "4. What is a content delivery network (CDN)?",
    "answer": "A content delivery network (CDN) is a distributed system of servers strategically placed across the globe to deliver web content (e.g., HTML, images, videos) to registers more quickly and efficiently. CDNs minimize delays in loading web page content by caching and delivering it from the server geographically closest to the user."
    },
    {
    "question": "5. What are some common performance optimization techniques for web applications?",
    "answer": "Some common performance optimization techniques include: Reducing HTTP requests by combining files, using sprites, inlining CSS and JavaScript; Minimizing file sizes through minification, gzip compression and image optimization; Caching assets on the client-side and server-side; Using a CDN to reduce latency; Improving server response time."
    },
    {
    "question": "6. What is cross-origin resource sharing (CORS)?",
    "answer": "Cross-origin resource sharing (CORS) is a security feature that enables web applications from one domain to request resources, like APIs or scripts, from a domain different from their own. CORS works by adding specific HTTP headers to control which origins have access to the resources and under what conditions."
    },
    {
    "question": "7. What is the purpose of HTML, CSS, and JavaScript in web development?",
    "answer": "HTML (HyperText Markup Language) is used to structure content on the web, while CSS (Cascading Style Sheets) is responsible for styling and layout, making the content visually appealing. JavaScript is a programming language that adds interactive functionality to websites, such as form validation, animations, and communication with APIs."
    },
    {
    "question": "8. What does the box model in CSS represent?",
    "answer": "The CSS box model is a rectangular layout paradigm that describes the composition of every HTML element on a web page. It consists of four parts: the content, padding (the space between the content and border), border (the edge around the padding), and margin (the space surrounding the border)."
    },
    {
    "question": "9. What is event propagation in JavaScript?",
    "answer": "Event propagation is the flow of event processing through the DOM (document object model) tree. It consists of three phases: capturing (the event flows from the top of the tree towards the target element), target (the event reaches the target element), and bubbling (the event flows back up the tree from the target element). Developers can control this propagation through stopPropagation() and preventDefault()."
    },
    {
    "question": "10. What is the document object model (DOM)?",
    "answer": "The document object model (DOM) is a programming interface for HTML and XML documents that represents the structure of a document as a tree of objects. Each object represents a part of the document, such as an element, attribute, or text node. DOM allows developers to interact with and manipulate web pages' structure, content, and style using scripting languages like JavaScript."
    },
    {
    "question": "11. How can you achieve progressive rendering in web applications?",
    "answer": "Progressive rendering involves breaking down a web page into smaller, more manageable pieces, and then prioritizing the rendering of the most important content first. Methods to achieve progressive rendering include asynchronous loading of resources, lazy loading of images, and using server-side rendering for initial page loads."
    },
    {
    "question": "12. What are the benefits of using CSS pre- and post-processors?",
    "answer": "CSS pre-processors, like Sass, Less, and Stylus, extend CSS with features like variables, mixins, and nested rules, making it more maintainable and less repetitive. CSS post-processors, like Autoprefixer and PostCSS, help with vendor-prefix handling, adding polyfills, and optimizing the CSS for better performance."
    },
    {
    "question": "13. How do you handle issues with browser compatibility?",
    "answer": "To handle browser compatibility issues, you should: Use feature detection with tools like Modernizr to provide fallbacks or polyfills for unsupported features; Implement progressive enhancement and graceful degradation techniques; Use CSS reset or normalize.css to maintain consistent styles across browsers; Test your application using different browsers and devices."
    },
    {
    "question": "14. What are the different ways to implement secure authentication in web applications?",
    "answer": "Secure authentication in web applications can be implemented using techniques like: Securely storing passwords using hashing and salting techniques, such as bcrypt; Implementing two-factor authentication (2FA); Using secure password reset processes, with tokens and expiration time limits; Employing HTTPS to encrypt data communication between client and server."
    },
    {
    "question": "15. Explain web components and their benefits",
    "answer": "Web components are a set of web platform APIs that enable developers to create reusable, modular, and encapsulated custom HTML elements. The benefits of web components include: Enhanced reusability and maintainability of code; Reduced dependencies on external libraries and frameworks; Easier to style and theme, providing better consistency in UI; Improved performance by reducing DOM complexity."
    },
    {
    "question": "16. What is the difference between React and Angular?",
    "answer": "React is a JavaScript library created by Facebook, primarily used for building fast and responsive user interfaces. It's focused on a component-based architecture and leverages a virtual DOM, enabling efficient updates and rendering. Angular, developed by Google, is a full-fledged framework that provides a complete solution for building dynamic single-page applications. It follows a declarative programming approach, uses a real DOM, and offers tools like dependency injection, two-way data binding, and a built-in module system."
    },
    {
    "question": "17. What is XSS, and how can you prevent it?",
    "answer": "Cross-site scripting (XSS) is a type of security vulnerability that lets attackers inject malicious scripts into web pages, leading to unauthorized access, data theft, and other harmful consequences. To prevent XSS, you need to: Validate and sanitize user inputs and outputs; Implement a content security policy (CSP) to restrict the sources of scripts and other resources; Use secure methods like textContent instead of innerHTML for DOM manipulation."
    },
    {
    "question": "18. Explain the concept of server-side rendering (SSR) vs. client-side rendering (CSR)",
    "answer": "Server-side rendering (SSR) is the process where the server generates a full HTML page for the initial request, improving the first meaningful paint and SEO. Client-side rendering (CSR) occurs when the browser loads an empty HTML document and then renders the content using JavaScript. CSR might lead to a slower initial load but enables better interactivity, faster subsequent page loads, and easier development of single-page applications (SPAs)."
    },
    {
    "question": "19. What is asset bundling, and why is it important?",
    "answer": "Asset bundling combines multiple CSS, JavaScript, and other files into single or few minified files. This process reduces the number of HTTP requests, improving load times and enhancing performance. It also helps with cache management, versioning, and organizing code."
    },
    {
    "question": "20. Explain the concept of server push in HTTP/2",
    "answer": "Server push is a feature in HTTP/2 that allows the server to proactively and asynchronously send resources to the client's cache, even before they are requested. This helps reduce latency, particularly for content that the server knows will be needed by the client, such as CSS and JavaScript"}
    
   ],
    "Data_science": [
           {
    "question": "Describe supervised and unsupervised learning and their differences",
    "answer": "A supervised learning model is instructed on a dataset that contains both an input variable (X) and an output variable (Y). The model learns from this data and makes predictions accordingly.\n\nAlternatively, unsupervised learning seeks to identify previously unknown patterns in a dataset without pre-existing labels, requiring minimal human supervision. It primarily focuses on discovering the underlying structure of the data."
    },
    {
    "question": "Can you explain overfitting and how to avoid it?",
    "answer": "Overfitting is a concept in data science where a statistical model fits the data too well. It means that the model or the algorithm fits the data too well to the training set. It may need to fit additional data and predict future observations reliably. Overfitting can be avoided using techniques like cross-validation, regularization, early stopping, pruning, or simply using more training data."
    },
    {
    "question": "What is the role of data cleaning in data analysis?",
    "answer": "Data cleaning involves checking for and correcting errors, dealing with missing values, and ensuring the data is consistent and accurate. With clean data, the analysis results could be balanced and accurate."
    },
    {
    "question": "What is a decision tree?",
    "answer": "A decision tree is a popular and intuitive machine learning algorithm which is most frequently used for regression and classification tasks. It is a graphical representation that uses a tree-like model of decisions and their possible consequences. The decision tree algorithm is established on the divide-and-conquer strategy, where it recursively divides the data into subsets considering the values of the input features until a stopping criterion is met."
    },
    {
    "question": "Describe the difference between a bar chart and a histogram",
    "answer": "A bar chart and a histogram both provide a visual representation of data. A bar chart is used for comparing different categories of data with the help of rectangular bars, when the length of the bar is proportional to the data value. The categories are usually independent. On the other hand, a histogram is used to represent the frequency of numerical data by using bars. The categories in a histogram are ranges of data, which makes it useful for understanding the data distribution."
    },
    {
    "question": "What is the central limit theorem, and why do we use it?",
    "answer": "The central limit theorem is a cornerstone principle in statistics that states that when an adequately big number of independent, identically distributed random variables are added, their sum tends toward a normal distribution, not considering the shape of the original distribution. This theorem is crucial because it allows us to make inferences about the means of different samples. It underpins many statistical methods, including confidence intervals and hypothesis testing."
    },
    {
    "question": "Can you explain what principal component analysis (PCA) is?",
    "answer": "Principal component analysis (PCA) is a statistical process which converts a set of observations of correlated variables into uncorrelated ones known as principal components. This technique is used to emphasize variation and identify strong patterns in a dataset by reducing its dimensionality while retaining as much information as possible. This makes it easier to visualize and analyze the data, as well as to identify important features and correlations. The principal components are linear combinations of the original variables and are chosen to capture the maximum amount of variation in the data. The first principal component is responsible for the biggest possible variance in the data, with each succeeding component accounting for the highest possible remaining variance while being orthogonal to the preceding components."
    },
    {
    "question": "Can you describe the difference between a box plot and a histogram?",
    "answer": "A box plot and a histogram are both graphical representations of data, but they present data in different ways. A box plot is a method used to depict groups of numerical data graphically through their quartiles, providing a sketch of the distribution of the data. It can also identify outliers and what their values are. On the other hand, a histogram is for plotting the frequency of score occurrences in a continuous dataset that has been divided into classes, called bins."
    },
    {
    "question": "What is the difference between correlation and covariance?",
    "answer": "Correlation and covariance are both measures used in statistics to describe the relationship between two variables, but they have some key differences.\n\nCovariance measures the extent to which two variables change together. It indicates the direction of the linear relationship between the variables. A positive covariance means that as one variable increases, the other variable tends to increase as well, while a negative covariance means that as one variable increases, the other variable tends to decrease. However, the magnitude of covariance depends on the scale of the variables, making it difficult to compare covariances between different datasets.\n\nCorrelation, on the other hand, standardizes the measure of the relationship between two variables, making it easier to interpret. Correlation coefficients range from -1 to 1, where -1 indicates a perfect negative linear relationship, 0 indicates no linear relationship, and 1 indicates a perfect positive linear relationship. Unlike covariance, correlation is dimensionless and does not depend on the scale of the variables, making it a more reliable measure for comparing relationships across different datasets."
    },
    {
    "question": "Explain what a random forest is",
    "answer": "Random forests are a machine learning algorithm consisting of multiple decision trees working together as an ensemble. The algorithm uses a random subset of features and data samples to train each individual tree, making the ensemble more diverse and less prone to overfitting.\n\nOne of the advantages of a random forest is its ability to produce class predictions based on the output of each tree, with the final prediction being the class with the majority of votes. The idea behind random forests is based on the notion that multiple weak learners can be combined to form a strong learner, with each tree contributing its own unique perspective to the overall prediction."
    },
    {
    "question": "What is the concept of bias and variance in machine learning?",
    "answer": "In machine learning, bias and variance are two crucial concepts that significantly affect a model's prediction error. The concept of bias refers to the error introduced by approximating a highly complex real-world problem using a much simpler model. The degree of bias can vary depending on how much the model oversimplifies the problem, leading to underfitting, which means that the model cannot capture the underlying patterns in the data. High bias means the model is too simple and may not capture important patterns in the data.\n\nOn the other hand, variance refers to the error introduced by the model's complexity. A model with high variance overcomplicates the problem, leading to overfitting, which means the model becomes too complex and captures the noise in the data instead of the underlying patterns. High variance means the model is too sensitive to the training data and may not generalize well to new, unseen data.\n\nFinding the right balance between variance and bias is crucial in creating an accurate and reliable model that can generalize well to new data."
    },
    {
    "question": "Can you explain what cross-validation is?",
    "answer": "Cross-validation is a powerful and widely used resampling technique in machine learning that is employed for assessing a model's performance on an independent data set and to fine-tune its hyperparameters. The primary objective of cross-validation is to prevent overfitting, a common problem in machine learning, by testing the model on unseen data.\n\nA common type of cross-validation is k-fold cross-validation, that involves dividing the data set into k subsets, or folds. The model is later trained on k-1 folds, and the remaining fold is used as a test set to evaluate the model's performance. This process is repeated k times, with each fold used exactly once as a test set.\n\nThe primary advantage of k-fold cross-validation is that it provides a more accurate and robust estimate of the model's true performance than a single train-test split.\n\nOverall, cross-validation is an essential tool in the machine learning practitioner's toolkit as it helps avoid overfitting and improves the reliability of the model's performance estimates."
    },
    
    {"question": "Describe precision and recall metrics, and their relationship to the ROC curve",
    "answer": "Precision and recall are two critical metrics used in evaluating the performance of a classification model, particularly in situations with imbalanced classes. Precision measures the accuracy of the positive predictions. In other words, it is the ratio of true positive results to all positive predictions (i.e., the sum of true positives and false positives). This metric answers the question,  Recall, also known as sensitivity or true positive rate, measures the ability of the classifier to find all the positive samples. It is the ratio of true positive results to the sum of true positives and false negatives. This means it answers the question."
    }
    ],
    "devops": [
        {
            "question": "What is containerization, and how does it differ from virtualization?",
            "answer": "Containerization is an operating system-level virtualization method for running multiple isolated applications on a single host. Unlike traditional virtualization, containers share the host's kernel and do not require a separate operating system for each instance."
        },
        {
            "question": "What is the purpose of a load balancer in a web application architecture?",
            "answer": "A load balancer distributes incoming network traffic across multiple servers or instances to optimize resource utilization, maximize throughput, minimize response time, and ensure fault tolerance."
        }
    ]
}

@app.route('/interview_prep')
def interview_prep():
    return render_template('interview_prep.html')

@app.route('/get_interview_questions')
def get_interview_questions():
    job_position = request.args.get('job_position')
    if job_position in interview_questions:
        return jsonify(interview_questions[job_position])
    else:
        return jsonify([])


if __name__ == '__main__':
    app.run(debug=True)
