// // Inline JavaScript for adding hover effect to top container links
// const topLinks = document.querySelectorAll('.top-container a');
// topLinks.forEach(link => {
//   link.addEventListener('mouseenter', () => {
//     link.style.color = '#007bff'; // Change color on hover
//   });
//   link.addEventListener('mouseleave', () => {
//     link.style.color = '#333'; // Revert color on mouse leave
//   });
// });

// // Smooth scrolling for anchor links
// document.querySelectorAll('a[href^="#"]').forEach(anchor => {
//   anchor.addEventListener('click', function (e) {
//     e.preventDefault();

//     document.querySelector(this.getAttribute('href')).scrollIntoView({
//       behavior: 'smooth'
//     });
//   });
// });



// //-- JavaScript for finding jobs and displaying job recommendations -->

//   document.getElementById('findJobs').addEventListener('click', function() {
//     // Simulated job recommendations data (replace with actual data from server)
//     var jobData = [
//       { title: 'Data Analyst', company: 'Data Corp', location: 'Chicago' },
//       { title: 'Marketing Manager', company: 'Marketing Solutions', location: 'Los Angeles' }
//       // Add more job data as needed
//     ];

//     // Clear previous job recommendations if any
//     var jobRecommendations = document.getElementById('jobRecommendations');
//     jobRecommendations.querySelector('tbody').innerHTML = '';

//     // Populate job recommendations table
//     jobData.forEach(function(job) {
//       var row = '<tr><td>' + job.title + '</td><td>' + job.company + '</td><td>' + job.location + '</td></tr>';
//       jobRecommendations.querySelector('tbody').innerHTML += row;
//     });

//     // Show job recommendations
//     jobRecommendations.style.display = 'block';
//   });
