# Software Requirements Specification (SRS)

## 1. Introduction

### 1.1 Purpose
The purpose of this web application is to provide a pre-assessment tool for students enrolling in JAMK programs. The tool will present multiple-choice and other question types to assess students’ skills, interests, and readiness for specific courses. Automated scoring and instant feedback will be provided, and results will be accessible to both students and teachers.

### 1.2 Scope
- Accessible via desktop and mobile.
- Supports multiple question formats (multiple-choice, input, range).
- Dynamic and randomized questions.
- Automated scoring and instant feedback.
- User authentication (JAMK credentials).
- Role-based access (student/teacher).
- Result review and recommendations.
- Admin/teacher can manage questions, courses, and feedback.

### 1.3 Definitions
- **eRPL Accreditation**: Recognition of prior learning.
- **Survey**: A set of questions mapped to one or more courses/skills.

---

## 2. Functional Requirements

### 2.1 User Registration & Authentication
- Students and teachers register/login using JAMK credentials.
- Roles: student, teacher.

### 2.2 Survey Management
- Teachers can create/edit surveys, add questions, and map them to courses/skills.
- Questions can be multiple-choice, input, or range.
- Questions can be randomized or dynamically shown based on previous answers.
- Teachers should have the ability to copy survey link and shared to students

### 2.3 Assessment Flow
- Students access the survey via a link in the program description (active during enrollment).
- Students answer questions and submit the survey.
- Automated scoring and instant feedback are provided upon submission.
- Results are saved and visible to both students and teachers.

### 2.4 Scoring & Feedback
- Each question/course/skill has associated scoring and feedback rules.
- Feedback is shown based on score thresholds (e.g., “lt”/“gt” comparisons).
- Three result cases: recommended to take the course, eligible for eRPL, or not suitable.
- The scores for questions should be standardized 0-10.
- The scores for Course should be scaled after doing the addition of the scores and shown in percentage. Example: there are 20 questions in a course, max score for the course is 200, and if the student gets 160 score then the final score would be (160/200)*100 percent.
- And the survey should also have the same style of criteria for all evaluation for all the courses overall, this can be useful for module(multiple courses) competency assessment.

### 2.5 Result Management
- All assessment results are stored and can be reviewed by teachers and students.
- Teachers can view aggregated results for their courses.

---

## 3. Non-Functional Requirements

- Responsive web design.
- Secure authentication and data storage.
- Scalable and maintainable codebase (FastAPI backend, React frontend).
- Dockerized deployment.

---

## 4. MongoDB Schema Proposal

### 4.1 Users
```json
{
  "_id": ObjectId,
  "photo_url": String,
  "display_name": String,
  "username": String, // or email
  "password_hash": String,
  "role": "student" | "teacher"
}
```

### 4.2 Courses (Skills)
```json
{
  "_id": ObjectId,
  "name": String,
  "code": String,
  "description": String
}
```

### 4.3 Questions
```json
{
  "_id": ObjectId,
  "answer_type": "multiple" | "input" | "choice" | "range",
  "title": String,
  "details": String,
  "correct_answers_and_scores": Object, // e.g., { "a": 0, "b": 1, "c": 3 } or { "input": "Jyvaskyla" }
  "feedbacks_based_on_score_default": [
    {
      "score": { "value": Number, "comparison": "lt" | "gt" },
      "feedback": String
    }
  ]
}
```

### 4.4 QuestionCourseAssociation
```json
{
  "_id": ObjectId,
  "course_id": ObjectId,
  "question_id": ObjectId,
  "answer_association_type": "positive" | "negative",
  "feedbacks_based_on_score": [
    {
      "score": { "value": Number, "comparison": "lt" | "gt" },
      "feedback": String
    }
  ]
}
```

### 4.5 Surveys
```json
{
  "_id": ObjectId,
  "title": String,
  "description": String,
  "course_skill_ids": [ObjectId], // references to Courses
  "course_skill_total_scores": [Number],
  "feedbacks_based_on_score_default": [
    {
      "course_skill_id": ObjectId,
      "score": { "value": Number, "comparison": "lt" | "gt" },
      "feedback": String
    }
  ]
}
```

### 4.6 StudentTakenSurveys
```json
{
  "_id": ObjectId,
  "survey_id": ObjectId,
  "student_id": ObjectId,
  "is_submitted": Boolean,
  "course_skill_scores": { "course_skill_id": Number } // e.g., { "Python": 25, "IoT": 10 }
}
```

### 4.7 StudentAnswers
```json
{
  "_id": ObjectId,
  "question_course_association_id": ObjectId,
  "survey_id": ObjectId,
  "student_id": ObjectId,
  "answer": Mixed, // type depends on question
  "is_submitted": Boolean
}
```

---

## 5. User Flow

1. Student logs in with JAMK credentials.
2. Student accesses the pre-assessment link (active during enrollment).
3. Student completes the survey (dynamic/randomized questions).
4. Upon submission, instant feedback and recommendations are shown.
5. Results are saved and visible to both student and teacher.
6. Teacher can review all results and provide further feedback if needed.
