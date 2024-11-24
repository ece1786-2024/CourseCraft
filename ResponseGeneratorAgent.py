import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("Error: OPENAI_API_KEY is not set in the environment variables.")
    exit(1)

client = OpenAI(api_key=OPENAI_API_KEY)

class ResponseGeneratorAgent:
    def __init__(self, max_tokens=4096):
        self.model_id = "gpt-3.5-turbo"  
        self.max_tokens = max_tokens
        
        # the 
        self.sys_prompt = """ 
        You are a specialized assistant at the University of Toronto, helping new students select courses based 
        on their requirements and a list of course info retrieved by a RAG system. 
        The RAG retrieved course info will contain several parts:
            1. The course code and the course name
            2. The course description
            3. The course prerequisites 
            4. The course offerings
            5. The meeting sections

        Use the RAG retrieved course info as your primary source of factual knowledge. Your generated recommendation
        should roughly follow the following format:
            1. Start with a friendly greeting and a concise summary of the user need based on the user query.
            2. Then start recommending courses one by one based on the five parts presented in RAG retrieved 
            course info. Based on the user need and the course info, explain why each course is recommended.
            3. Summarize the recommended courses and come up with an overall summary for the learning path.
            4. Finish up by another friendly message and prompt for more instructions.
            
        Always follow these rules:
            1. Don't reveal info about the RAG system.
            2. Be professional, friendly, curious, and helpful.
            3. **Ensure that each course description follows the specified example format below:**
            **Example Format:**
            ```
            [
                {
                    "course_code": "CSC108",
                    "name": "Introduction to Computer Programming",
                    "department": "Computer Science",
                    "division": "Faculty of Arts & Science",
                    "description": "An introduction to programming using Python...",
                    "prerequisites": "None",
                    "exclusions": "CSC148, CSC150",
                    "campus": "St. George",
                    "section_code": "F",
                    "meeting_sections": ["Lecture: Mon/Wed/Fri 10-11 AM", "Tutorial: Thu 2-3 PM"]
                }
            ]  
            ```
            You must strictly follow this format for each course you recommend.
            
        **Summary:**
        Your primary role is to engage new students in a supportive and informative dialogue, patiently eliciting the necessary
        information to provide tailored course recommendations. Always prioritize the student's comfort and understanding, ensuring that 
        the conversation remains open and student-centered.
        """
        self.messages = [{"role": "system", "content": self.sys_prompt}]

    def generate_response(self, user_query, retrieved_courses):
        # Add user query and retrieved courses to the conversation
        self.messages.append({
            "role": "user",
            "content": f"""
            User Query: {user_query}
            Retrieved Courses: {retrieved_courses}
            Now starts your recommendations.
            """
        })

        try:
            response = client.chat.completions.create(
                model=self.model_id,
                messages=self.messages,
                max_tokens=self.max_tokens,
                temperature=0.7
            )
            #print("Response generated successfully.")
            return response.choices[0].message.content
        except Exception as e:
            print("Error during response generation:", str(e))
            return "Sorry, I couldn't generate a response at this time."



if __name__ == "__main__":
    agent = ResponseGeneratorAgent()
    user_query = "I'm a first-year student interested in introductory computer science courses."
    retrieved_courses = [
        #"Course: CSC108 - Introduction to Computer Programming\nDescription: An introduction to programming using Python.",
        #"Course: CSC148 - Introduction to Computer Science\nDescription: Basic data structures and algorithms.",
        """This course RSM358H1 - 'Foundations of AI for Management' is offered by the Rotman Commerce department in the Arts and Science, Faculty of.
                Course Description: Artificial intelligence — the application of machine-learning techniques to prediction problems historically performed by humans — is transforming business and society. This course provides a hands-on introduction to the wide variety of algorithms used in applications of machine-learning. The technical topics will include linear and non-linear regression models, classification algorithms, and more recent machine-learning techniques rooted in neuroscience like reinforcement learning and deep learning. Application topics will include predicting consumer choices, MLB salaries, and Super Mario Bros. There will be an emphasis on conceptual understanding, so that students can interpret the results of these techniques to support effective decision-making. The course will be complemented by many hands-on exercises using the R programming language.
                Understanding the course code: RSM358H1: The first three letters represent the department (RSM),
                and the section code F indicates when it's offered - 'F' means Fall semester (September-December),
                'S' means Winter semester (January-April), and 'Y' means full year course.
                Prerequisites required: ECO220Y1/ECO227Y1/(STA220H1, STA255H1)/(STA237H1, STA238H1)/(STA257H1, STA261H1), CSC108H1/CSC148H1 
                Exclusions: RSM338H1, RSM313H1 (Special Topics in Management: Foundations of Artificial Intelligence for Management), offered in Fall 2020
                This course is offered at the St. George campus during these sessions: N/A.
                Meeting Sections: Section: LEC0101, Type: Lecture, Instructors: Ryan Webb, Times: Day 2, 15:00:00-17:00:00 at RT, Class Size: 50
Section: LEC0201, Type: Lecture, Instructors: Ryan Webb, Times: Day 5, 13:00:00-15:00:00 at WO, Class Size: 55
                
---
This course CSC384H5 - 'Introduction to Artificial Intelligence' is offered by the Department of Mathematical and Computational Sciences department in the University of Toronto Mississauga.
                Course Description: Theories and algorithms that capture (or approximate) some of the core elements of computational intelligence. Topics include: search, logical representations and reasoning, classical automated planning, representing and reasoning with uncertainty, learning, decision making (planning) under uncertainty. Assignments provide practical experience, in both theory and programming, of the core topics.
                Understanding the course code: CSC384H5: The first three letters represent the department (CSC),
                and the section code F indicates when it's offered - 'F' means Fall semester (September-December),
                'S' means Winter semester (January-April), and 'Y' means full year course.
                Prerequisites required: <p>CSC263H5 and (STA246H5 or STA256H5 or STA237H1 or STA238H1 or ECO227Y5 or ECE286H1)</p>
                Exclusions: CSC384H1 or CSCD84H3
                This course is offered at the University of Toronto at Mississauga campus during these sessions: N/A.
                Meeting Sections: Section: LEC0101, Type: Lecture, Instructors: Randy Hickey, Times: Day 2, 09:00:00-11:00:00 at MN, Class Size: 80
Section: LEC0102, Type: Lecture, Instructors: Randy Hickey, Times: Day 3, 17:00:00-19:00:00 at IB, Class Size: 80
                
---
This course MIE369H1 - 'Introduction to Artificial Intelligence' is offered by the Department of Mechanical & Industrial Engineering department in the Applied Science & Engineering, Faculty of.
                Course Description: Introduction to Artificial Intelligence. Search. Constraint Satisfaction. Propositional and First-order Logic Knowledge Representation. Representing Uncertainty (Bayesian networks). Rationality and (Sequential) Decision Making under Uncertainty. Reinforcement Learning. Weak and Strong AI, AI as Engineering, Ethics and Safety in AI.
                Understanding the course code: MIE369H1: The first three letters represent the department (MIE),
                and the section code S indicates when it's offered - 'F' means Fall semester (September-December),
                'S' means Winter semester (January-April), and 'Y' means full year course.
                Prerequisites required: MIE250H1/ECE244H1/ECE345H1/CSC263H1/CSC265H1, MIE236H1/ECE286H1/ECE302H1
                Exclusions: ROB311H1, CSC384H1
                This course is offered at the St. George campus during these sessions: N/A.
                Meeting Sections: Section: LEC0101, Type: Lecture, Instructors: Scott Sanner, Times: Day 1, 15:00:00-16:00:00 at BA, Day 4, 16:00:00-18:00:00 at BA, Class Size: 60
                
---
This course STAD78H3 - 'Machine Learning Theory' is offered by the Dept. of Computer & Mathematical Sci (UTSC) department in the University of Toronto Scarborough.
                Course Description: Presents theoretical foundations of machine learning. Risk, empirical risk minimization, PAC learnability and its generalizations, uniform convergence, VC dimension, structural risk minimization, regularization, linear models and their generalizations, ensemble methods, stochastic gradient descent, stability, online learning.
                Understanding the course code: STAD78H3: The first three letters represent the department (STA),
                and the section code F indicates when it's offered - 'F' means Fall semester (September-December),
                'S' means Winter semester (January-April), and 'Y' means full year course.
                Prerequisites required: STAB57H3 and STAC62H3
                Exclusions: None
                This course is offered at the Scarborough campus during these sessions: N/A.
                Meeting Sections: Section: LEC01, Type: Lecture, Instructors: Daniel Roy, Times: Day 2, 11:00:00-14:00:00 at BV, Class Size: 50
                
---
This course CSC384H1 - 'Introduction to Artificial Intelligence' is offered by the Department of Computer Science department in the Arts and Science, Faculty of.
                Course Description: Theories and algorithms that capture (or approximate) some of the core elements of computational intelligence. Topics include: search; logical representations and reasoning, classical automated planning, representing and reasoning with uncertainty, learning, decision making (planning) under uncertainty. Assignments provide practical experience, in both theory and programming, of the core topics.
                Understanding the course code: CSC384H1: The first three letters represent the department (CSC),
                and the section code F indicates when it's offered - 'F' means Fall semester (September-December),
                'S' means Winter semester (January-April), and 'Y' means full year course.
                Prerequisites required: <p>(CSC263H1/​ CSC265H1/ CSC263H5/ CSCB63H3/ <a href="https://engineering.calendar.utoronto.ca/course/ece345h1" target="_blank">ECE345H1</a>/ <a href="https://engineering.calendar.utoronto.ca/course/ece358h1" target="_blank">ECE358H1</a>/ MIE245H1/ (CSC148H1, enrolled in ASMAJ1446A, completed at least 9.0 credits), STA220H1/ STA237H1/ STA247H1/​ STA255H1/​ STA257H1/ STAB57H3/ STAB52H3/ <a href="https://engineering.calendar.utoronto.ca/course/ece302h1" target="_blank">ECE302H1</a>/ STA286H1/ <a href="https://engineering.calendar.utoronto.ca/course/che223h1" target="_blank">CHE223H1</a>/ <a href="https://engineering.calendar.utoronto.ca/course/cme263h1" target="_blank">CME263H1</a>/ <a href="https://engineering.calendar.utoronto.ca/course/mie231h1" target="_blank">MIE231H1</a>/ <a href="https://engineering.calendar.utoronto.ca/course/mie236h1" target="_blank">MIE236H1</a>/ <a href="https://engineering.calendar.utoronto.ca/course/mse238h1" target="_blank">MSE238H1</a>/ <a href="https://engineering.calendar.utoronto.ca/course/ece286h1" target="_blank">ECE286H1</a>/ PSY201H1)</p>
                Exclusions: <p>CSC384H5, CSCD84H3, MIE369H1. NOTE: Students not enrolled in the Computer Science Major or Specialist program at A&amp;S, UTM, or UTSC, or the Data Science Specialist at A&amp;S, are limited to a maximum of 1.5 credits in 300-/400-level CSC/ECE courses.</p>
                This course is offered at the St. George campus during these sessions: N/A.
                Meeting Sections: Section: LEC0201, Type: Lecture, Instructors: Alice Gao, Times: Day 1, 14:00:00-15:00:00 at MP, Day 3, 14:00:00-15:00:00 at MP, Day 5, 14:00:00-15:00:00 at MP, Class Size: 90
Section: LEC2101, Type: Lecture, Instructors: Alice Gao, Times: Day 1, 14:00:00-15:00:00 at MP, Day 3, 14:00:00-15:00:00 at MP, Day 5, 14:00:00-15:00:00 at MP, Class Size: 35
Section: LEC0101, Type: Lecture, Instructors: Alice Gao, Times: Day 1, 12:00:00-13:00:00 at BA, Day 3, 12:00:00-13:00:00 at BA, Day 5, 12:00:00-13:00:00 at BA, Class Size: 90
Section: LEC2001, Type: Lecture, Instructors: Alice Gao, Times: Day 1, 12:00:00-13:00:00 at BA, Day 3, 12:00:00-13:00:00 at BA, Day 5, 12:00:00-13:00:00 at BA, Class Size: 35
                
---
This course CSCD84H3 - 'Artificial Intelligence' is offered by the Dept. of Computer & Mathematical Sci (UTSC) department in the University of Toronto Scarborough.
                Course Description: A study of the theories and algorithms of Artificial Intelligence. Topics include a subset of: search, game playing, logical representations and reasoning, planning, natural language processing, reasoning and decision making with uncertainty, computational perception, robotics, and applications of Artificial Intelligence. Assignments provide practical experience of the core topics.
                Understanding the course code: CSCD84H3: The first three letters represent the department (CSC),
                and the section code S indicates when it's offered - 'F' means Fall semester (September-December),
                'S' means Winter semester (January-April), and 'Y' means full year course.
                Prerequisites required: STAB52H3 and CSCB63H3 and [a CGPA of 3.5 or enrolment in a CSC subject POSt]
                Exclusions: CSC484H, CSC384H
                This course is offered at the Scarborough campus during these sessions: N/A.
                Meeting Sections: Section: LEC01, Type: Lecture, Instructors: Bryan Chan, Times: Day 1, 09:00:00-11:00:00 at SW, Class Size: 110
                
---
This course STAD68H3 - 'Advanced Machine Learning and Data Mining' is offered by the Dept. of Computer & Mathematical Sci (UTSC) department in the University of Toronto Scarborough.
                Course Description: Statistical aspects of supervised learning: regression, regularization methods, parametric and nonparametric classification methods, including Gaussian processes for regression and support vector machines for classification, model averaging, model selection, and mixture models for unsupervised learning. Some advanced methods will include Bayesian networks and graphical models.
                Understanding the course code: STAD68H3: The first three letters represent the department (STA),
                and the section code S indicates when it's offered - 'F' means Fall semester (September-December),
                'S' means Winter semester (January-April), and 'Y' means full year course.
                Prerequisites required: CSCC11H3 and STAC58H3 and STAC67H3
                Exclusions: 
                This course is offered at the Scarborough campus during these sessions: N/A.
                Meeting Sections: Section: LEC01, Type: Lecture, Instructors: Sotirios Damouras, Times: Day 3, 14:00:00-15:00:00 at BV, Day 5, 13:00:00-15:00:00 at IA, Class Size: 60
                
---
This course ECE324H1 - 'Machine Intelligence, Software and Neural Networks' is offered by the Division of Engineering Science department in the Applied Science & Engineering, Faculty of.
                Course Description: An introduction to machine learning engineering, with a focus on neural networks. The entire process of developing a machine learning solution, from data collection to software development, as well as ethics in machine learning, will be discussed. Practical techniques in machine learning will be covered, including data augmentation and the use of pre-trained networks. Topics covered will include the fundamentals of neural networks, convolutional neural networks, recurrent neural networks, generative adversarial networks and transformer networks. Students will complete a major hands-on project in machine learning.
                Understanding the course code: ECE324H1: The first three letters represent the department (ECE),
                and the section code S indicates when it's offered - 'F' means Fall semester (September-December),
                'S' means Winter semester (January-April), and 'Y' means full year course.
                Prerequisites required: <p>ESC190H1, ECE286H1, ECE421H1</p>
                Exclusions: APS360H1
                This course is offered at the St. George campus during these sessions: N/A.
                Meeting Sections: Section: LEC0101, Type: Lecture, Instructors: Benjamin Manuel Sanchez, Times: Day 2, 12:00:00-13:00:00 at WB, Day 4, 09:00:00-11:00:00 at BA, Class Size: 54
                
---
This course ROB311H1 - 'ARTIFICIAL INTELLIGENCE' is offered by the Division of Engineering Science department in the Applied Science & Engineering, Faculty of.
                Course Description: An introduction to the fundamental principles of artificial intelligence from a mathematical perspective. The course will trace the historical development of AI and describe key results in the field. Topics include the philosophy of AI, search methods in problem solving, knowledge representation and reasoning, logic, planning, and learning paradigms. A portion of the course will focus on ethical AI, embodied AI, and on the quest for artificial general intelligence.
                Understanding the course code: ROB311H1: The first three letters represent the department (ROB),
                and the section code S indicates when it's offered - 'F' means Fall semester (September-December),
                'S' means Winter semester (January-April), and 'Y' means full year course.
                Prerequisites required: <p>ECE286H1, ECE302H1 and ECE345H1, ECE358H1, CSC263H1</p>
                Exclusions: 
                This course is offered at the St. George campus during these sessions: N/A.
                Meeting Sections: Section: LEC0101, Type: Lecture, Instructors: Chandra Gummaluru, Times: Day 5, 15:00:00-17:00:00 at MY, Day 4, 13:00:00-15:00:00 at SF, Class Size: 72
                
---
This course CSC311H5 - 'Introduction to Machine Learning' is offered by the Department of Mathematical and Computational Sciences department in the University of Toronto Mississauga.
                Course Description: An introduction to methods for automated learning of relationships on the basis of empirical data. Classification and regression using nearest neighbour methods, decision trees, linear models, and neural networks. Clustering algorithms. Problems of overfitting and of assessing accuracy. Basics of reinforcement learning.
                Understanding the course code: CSC311H5: The first three letters represent the department (CSC),
                and the section code S indicates when it's offered - 'F' means Fall semester (September-December),
                'S' means Winter semester (January-April), and 'Y' means full year course.
                Prerequisites required: CSC207H5 and (MAT223H5 or MAT240H5) and MAT232H5 and (STA246H5 or STA256H5)
                Exclusions: CSC411H5 or CSC311H1 or CSCC11H3
                This course is offered at the University of Toronto at Mississauga campus during these sessions: N/A.
                Meeting Sections: Section: LEC0103, Type: Lecture, Instructors: Anthony Bonner, Times: Day 2, 09:00:00-11:00:00 at MN, Class Size: 80
Section: LEC0105, Type: Lecture, Instructors: Marina Tawfik, Times: Day 2, 17:00:00-19:00:00 at MN, Class Size: 80
Section: LEC0102, Type: Lecture, Instructors: Bilal Majed Taha, Times: Day 1, 15:00:00-17:00:00 at MN, Class Size: 80
Section: LEC0101, Type: Lecture, Instructors: Lisa Chenxue Zhang, Times: Day 1, 11:00:00-13:00:00 at MN, Class Size: 80
Section: LEC0104, Type: Lecture, Instructors: Mai Ha Vu, Times: Day 2, 13:00:00-15:00:00 at MN, Class Size: 80
                
---
This course CSCC11H3 - 'Introduction to Machine Learning and Data Mining' is offered by the Dept. of Computer & Mathematical Sci (UTSC) department in the University of Toronto Scarborough.
                Course Description: An introduction to methods for automated learning of relationships on the basis of empirical data. Classification and regression using nearest neighbour methods, decision trees, linear and non-linear models, class-conditional models, neural networks, and Bayesian methods. Clustering algorithms and dimensionality reduction. Model selection. Problems of over-fitting and assessing accuracy. Problems with handling large databases.
                Understanding the course code: CSCC11H3: The first three letters represent the department (CSC),
                and the section code F indicates when it's offered - 'F' means Fall semester (September-December),
                'S' means Winter semester (January-April), and 'Y' means full year course.
                Prerequisites required: MATB24H3 and MATB41H3 and STAB52H3 and [CGPA of at least 3.5 or enrolment in a CSC Subject POSt or enrolment in a non-CSC Subject POSt for which this specific course is a program requirement].
                Exclusions: CSC411H, (CSCD11H3)
                This course is offered at the Scarborough campus during these sessions: N/A.
                Meeting Sections: Section: LEC01, Type: Lecture, Instructors: Yiqing Irene Huang, Times: Day 5, 11:00:00-13:00:00 at SW, Class Size: 120
                
---
This course CSC384H1 - 'Introduction to Artificial Intelligence' is offered by the Department of Computer Science department in the Arts and Science, Faculty of.
                Course Description: Theories and algorithms that capture (or approximate) some of the core elements of computational intelligence. Topics include: search; logical representations and reasoning, classical automated planning, representing and reasoning with uncertainty, learning, decision making (planning) under uncertainty. Assignments provide practical experience, in both theory and programming, of the core topics.
                Understanding the course code: CSC384H1: The first three letters represent the department (CSC),
                and the section code S indicates when it's offered - 'F' means Fall semester (September-December),
                'S' means Winter semester (January-April), and 'Y' means full year course.
                Prerequisites required: <p>(CSC263H1/​ CSC265H1/ CSC263H5/ CSCB63H3/ <a href="https://engineering.calendar.utoronto.ca/course/ece345h1" target="_blank">ECE345H1</a>/ <a href="https://engineering.calendar.utoronto.ca/course/ece358h1" target="_blank">ECE358H1</a>/ MIE245H1/ (CSC148H1, enrolled in ASMAJ1446A, completed at least 9.0 credits), STA220H1/ STA237H1/ STA247H1/​ STA255H1/​ STA257H1/ STAB57H3/ STAB52H3/ <a href="https://engineering.calendar.utoronto.ca/course/ece302h1" target="_blank">ECE302H1</a>/ STA286H1/ <a href="https://engineering.calendar.utoronto.ca/course/che223h1" target="_blank">CHE223H1</a>/ <a href="https://engineering.calendar.utoronto.ca/course/cme263h1" target="_blank">CME263H1</a>/ <a href="https://engineering.calendar.utoronto.ca/course/mie231h1" target="_blank">MIE231H1</a>/ <a href="https://engineering.calendar.utoronto.ca/course/mie236h1" target="_blank">MIE236H1</a>/ <a href="https://engineering.calendar.utoronto.ca/course/mse238h1" target="_blank">MSE238H1</a>/ <a href="https://engineering.calendar.utoronto.ca/course/ece286h1" target="_blank">ECE286H1</a>/ PSY201H1)</p>
                Exclusions: <p>CSC384H5, CSCD84H3, MIE369H1. NOTE: Students not enrolled in the Computer Science Major or Specialist program at A&amp;S, UTM, or UTSC, or the Data Science Specialist at A&amp;S, are limited to a maximum of 1.5 credits in 300-/400-level CSC/ECE courses.</p>
                This course is offered at the St. George campus during these sessions: N/A.
                Meeting Sections: Section: LEC0101, Type: Lecture, Instructors: Bahar Aameri, Times: Day 1, 10:00:00-11:00:00 at MP, Day 3, 10:00:00-11:00:00 at BA, Day 5, 10:00:00-11:00:00 at KP, Class Size: 125
Section: LEC0301, Type: Lecture, Instructors: Bahar Aameri, Times: Day 3, 16:00:00-17:00:00 at BA, Day 5, 16:00:00-17:00:00 at BA, Day 1, 16:00:00-17:00:00 at SS, Class Size: 85
Section: LEC2501, Type: Lecture, Instructors: Christodoulos Karavasilis, Times: Day 2, 18:00:00-21:00:00 at BA, Class Size: 125
Section: LEC0201, Type: Lecture, Instructors: Bahar Aameri, Times: Day 1, 12:00:00-13:00:00 at BA, Day 3, 12:00:00-13:00:00 at BA, Day 5, 12:00:00-13:00:00 at MP, Class Size: 125
Section: LEC2001, Type: Lecture, Instructors: Bahar Aameri, Times: Day 3, 16:00:00-17:00:00 at BA, Day 5, 16:00:00-17:00:00 at BA, Day 1, 16:00:00-17:00:00 at SS, Class Size: 40
                
---
This course MIE370H1 - 'Introduction to Machine Learning' is offered by the Department of Mechanical & Industrial Engineering department in the Applied Science & Engineering, Faculty of.
                Course Description: Intro to Machine Learning, Hypothesis Spaces, Inductive Bias. Supervised Learning: Linear and Logistic Regression. Cross Validation (CV). Support Vector Machines (SVMs) and Regression. Empirical Risk Minimization and Regularization. Unsupervised Learning: Clustering and PCA. Decision Trees, Ensembles and Random Forest. Neural Net Fundamentals. Engineering Design considerations for Deployment: Explainability, Interpretability, Bias and Fairness, Accountability, Ethics, Feedback Loops, and Technical Debt.
                Understanding the course code: MIE370H1: The first three letters represent the department (MIE),
                and the section code F indicates when it's offered - 'F' means Fall semester (September-December),
                'S' means Winter semester (January-April), and 'Y' means full year course.
                Prerequisites required: <p>ECE286H1, or (MIE236H1/ECE302H1 and MIE237H1)</p>
                Exclusions: <p>CSC311H1, ECE421H1, ECE521H1, ROB313H1</p>
                This course is offered at the St. George campus during these sessions: N/A.
                Meeting Sections: Section: LEC0101, Type: Lecture, Instructors: Samin Aref, Times: Day 5, 10:00:00-12:00:00 at KP, Day 3, 09:00:00-10:00:00 at MC, Class Size: 120
                
---
This course STA314H5 - 'Introduction to Statistical Learning' is offered by the Department of Mathematical and Computational Sciences department in the University of Toronto Mississauga.
                Course Description: A thorough introduction to the basic ideas in supervised statistical learning with a focus on regression and a brief introduction to classification. Methods covered will include multiple linear regression and its extensions, k-nn regression, variable selection and regularization via AIC,BIC, Ridge and lasso penalties, non-parametric methods including basis expansions, local regression and splines, generalized additive models, tree-based methods, bagging, boosting and random forests. Content will be discussed from a statistical angle, putting emphasis on uncertainty quantification and the impact of randomness in the data on the outcome of any learning procedure. A detailed discussion of the main statistical ideas behind crossvalidation, sample splitting and re-sampling methods will be given. Throughout the course, R will be used as software, a brief introduction will be given in the beginning.
                Understanding the course code: STA314H5: The first three letters represent the department (STA),
                and the section code F indicates when it's offered - 'F' means Fall semester (September-December),
                'S' means Winter semester (January-April), and 'Y' means full year course.
                Prerequisites required: (MAT223H5 or MAT240H5) and (STA258H5 or ECO375H5) and STA260H5
                Exclusions: STA314H1
                This course is offered at the University of Toronto at Mississauga campus during these sessions: N/A.
                Meeting Sections: Section: LEC0101, Type: Lecture, Instructors: Stanislav Volgushev, Times: Day 2, 18:00:00-21:00:00 at IB, Class Size: 130
                
---
This course EDS285H5 - 'The Future of Ed Tech: Active Learning Classrooms and Artificial Intelligence' is offered by the Department of Language Studies department in the University of Toronto Mississauga.
                Course Description: This course will explore research on emerging digital models, learning pods, platforms, apps and policies that seek to further customize, enhance and bring greater equity to education through technology. From the initiation of open courseware, to the inception of virtual reality, artificial intelligence, ALC classrooms, makerspaces and the “shared economy”, this course will foster a culture of digital innovation to investigate, accelerate, test and study new possibilities and advancements in the field of educational technology.
                Understanding the course code: EDS285H5: The first three letters represent the department (EDS),
                and the section code F indicates when it's offered - 'F' means Fall semester (September-December),
                'S' means Winter semester (January-April), and 'Y' means full year course.
                Prerequisites required: 
                Exclusions: 
                This course is offered at the University of Toronto at Mississauga campus during these sessions: N/A.
                Meeting Sections: Section: LEC0101, Type: Lecture, Instructors: Paul Alexander, Times: Day 3, 15:00:00-17:00:00 at MN, Class Size: 55
                
---
This course EDS285H5 - 'The Future of Ed Tech: Active Learning Classrooms and Artificial Intelligence' is offered by the Department of Language Studies department in the University of Toronto Mississauga.
                Course Description: This course will explore research on emerging digital models, learning pods, platforms, apps and policies that seek to further customize, enhance and bring greater equity to education through technology. From the initiation of open courseware, to the inception of virtual reality, artificial intelligence, ALC classrooms, makerspaces and the “shared economy”, this course will foster a culture of digital innovation to investigate, accelerate, test and study new possibilities and advancements in the field of educational technology.
                Understanding the course code: EDS285H5: The first three letters represent the department (EDS),
                and the section code S indicates when it's offered - 'F' means Fall semester (September-December),
                'S' means Winter semester (January-April), and 'Y' means full year course.
                Prerequisites required: 
                Exclusions: 
                This course is offered at the University of Toronto at Mississauga campus during these sessions: N/A.
                Meeting Sections: Section: LEC0101, Type: Lecture, Instructors: Ji-young Shin, Times: Day 3, 16:00:00-18:00:00 at MN, Class Size: 55
                
---
This course CSCC11H3 - 'Introduction to Machine Learning and Data Mining' is offered by the Dept. of Computer & Mathematical Sci (UTSC) department in the University of Toronto Scarborough.
                Course Description: An introduction to methods for automated learning of relationships on the basis of empirical data. Classification and regression using nearest neighbour methods, decision trees, linear and non-linear models, class-conditional models, neural networks, and Bayesian methods. Clustering algorithms and dimensionality reduction. Model selection. Problems of over-fitting and assessing accuracy. Problems with handling large databases.
                Understanding the course code: CSCC11H3: The first three letters represent the department (CSC),
                and the section code S indicates when it's offered - 'F' means Fall semester (September-December),
                'S' means Winter semester (January-April), and 'Y' means full year course.
                Prerequisites required: MATB24H3 and MATB41H3 and STAB52H3 and [CGPA of at least 3.5 or enrolment in a CSC Subject POSt or enrolment in a non-CSC Subject POSt for which this specific course is a program requirement].
                Exclusions: CSC411H, (CSCD11H3)
                This course is offered at the Scarborough campus during these sessions: N/A.
                Meeting Sections: Section: LEC01, Type: Lecture, Instructors: Yiqing Irene Huang, Times: Day 2, 10:00:00-11:00:00 at IC, Day 4, 10:00:00-11:00:00 at IC, Class Size: 80
Section: LEC02, Type: Lecture, Instructors: Yiqing Irene Huang, Times: Day 2, 14:00:00-15:00:00 at SW, Day 4, 13:00:00-14:00:00 at IC, Class Size: 80
                
---
This course STAA57H3 - 'Introduction to Data Science' is offered by the Dept. of Computer & Mathematical Sci (UTSC) department in the University of Toronto Scarborough.
                Course Description: Reasoning using data is an integral part of our increasingly data-driven world. This course introduces students to statistical thinking and equips them with practical tools for analyzing data. The course covers the basics of data management and visualization, sampling, statistical inference and prediction, using a computational approach and real data.
                Understanding the course code: STAA57H3: The first three letters represent the department (STA),
                and the section code S indicates when it's offered - 'F' means Fall semester (September-December),
                'S' means Winter semester (January-April), and 'Y' means full year course.
                Prerequisites required: CSCA08H3
                Exclusions: STAB22H3, STA130H, STA220H
                This course is offered at the Scarborough campus during these sessions: N/A.
                Meeting Sections: Section: LEC01, Type: Lecture, Instructors: Shahriar Shams, Times: Day 5, 09:00:00-11:00:00 at IA, Day 3, 09:00:00-11:00:00 at IA, Class Size: 120
                
---
This course STA315H5 - 'Advanced Statistical Learning' is offered by the Department of Mathematical and Computational Sciences department in the University of Toronto Mississauga.
                Course Description: The second part of the course will focus on basic ideas in classification problems including discriminant analysis and support vector machine, and unsupervised learning techniques such as clustering, principal component analysis, independent component analysis and multidimensional scaling. The course will also cover the modern statistics in the "big data" area. The high dimensional problems when p >> n and n >> p will be introduced. In addition, the students will be formed as groups to do data analysis projects on statistical machine learning and present their findings in class. This will prepare them for future careers in industry or academia.
                Understanding the course code: STA315H5: The first three letters represent the department (STA),
                and the section code S indicates when it's offered - 'F' means Fall semester (September-December),
                'S' means Winter semester (January-April), and 'Y' means full year course.
                Prerequisites required: STA314H5
                Exclusions: 
                This course is offered at the University of Toronto at Mississauga campus during these sessions: N/A.
                Meeting Sections: Section: LEC0101, Type: Lecture, Instructors: Dehan Kong, Times: Day 2, 13:00:00-16:00:00 at MN, Class Size: 80
        """
    ]
    response = agent.generate_response(user_query, retrieved_courses)
    print("\nGenerated Response:\n", response)
