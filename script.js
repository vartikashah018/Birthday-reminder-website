document.addEventListener('DOMContentLoaded', function() {
    // Confirm before deleting
    const deleteButtons = document.querySelectorAll('.btn-danger');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this birthday?')) {
                e.preventDefault();
            }
        });
    });

    // Highlight today's birthdays
    const todayBadges = document.querySelectorAll('.badge.bg-success');
    todayBadges.forEach(badge => {
        badge.parentElement.parentElement.classList.add('table-success');
    });
});