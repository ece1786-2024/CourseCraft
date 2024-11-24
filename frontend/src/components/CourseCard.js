// CourseCard.jsx
import React from 'react';
import { Card, CardHeader, CardContent, CardActions, Typography, Button, IconButton, Collapse } from '@mui/material';
import { Favorite, ExpandMore } from '@mui/icons-material';

function CourseCard({ course, onAddToFavorites }) {
  const [expanded, setExpanded] = React.useState(false);

  const handleExpandClick = () => {
    setExpanded(!expanded);
  };

  return (
    <Card sx={{ maxWidth: 600, margin: '1rem auto' }}>
      <CardHeader
        title={`${course.course_code} - ${course.name}`}
        subheader={`${course.department} | ${course.division}`}
      />
      <CardContent>
        <Typography variant="body2" color="text.secondary">
          {course.description}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ marginTop: '0.5rem' }}>
          <strong>Prerequisites:</strong> {course.prerequisites || 'None'}
        </Typography>
      </CardContent>
      <CardActions disableSpacing>
        <IconButton aria-label="add to favorites" onClick={() => onAddToFavorites(course)}>
          <Favorite />
        </IconButton>
        <Button
          variant="text"
          endIcon={<ExpandMore />}
          onClick={handleExpandClick}
          aria-expanded={expanded}
          aria-label="show more"
        >
          {expanded ? 'Hide Details' : 'View More Details'}
        </Button>
      </CardActions>
      <Collapse in={expanded} timeout="auto" unmountOnExit>
        <CardContent>
          <Typography paragraph>
            <strong>Meeting Schedule:</strong>
          </Typography>
          {course.meeting_sections && course.meeting_sections.length > 0 ? (
            course.meeting_sections.map((section, index) => (
              <Typography key={index} variant="body2" color="text.secondary">
                {section}
              </Typography>
            ))
          ) : (
            <Typography variant="body2" color="text.secondary">
              No meeting sections available.
            </Typography>
          )}
        </CardContent>
      </Collapse>
    </Card>
  );
}

export default CourseCard;
