// CourseList.js
import React from 'react';
import CourseCard from './CourseCard';
import { Grid } from '@mui/material';

function CourseList({ courses }) {
  const handleAddToFavorites = (course) => {
    console.log(`Added ${course.course_code} to favorites.`);
  };

  return (
    <div>
      {courses.length > 0 ? (
        <Grid container spacing={2} justifyContent="center">
          {courses.map((course, index) => (
            <Grid item xs={12} sm={6} md={4} key={`${course.course_code}-${index}`}>
              <CourseCard
                course={course}
                onAddToFavorites={handleAddToFavorites}
              />
            </Grid>
          ))}
        </Grid>
      ) : (
        <p>No course recommendations available.</p>
      )}
    </div>
  );
}

export default CourseList;
