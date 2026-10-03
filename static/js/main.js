const expenseDeleteDialog = document.querySelector("#expense-delete-dialog");
const expenseDeleteConfirmButton = expenseDeleteDialog?.querySelector("[data-delete-confirm]");
const expenseDeleteCancelButton = expenseDeleteDialog?.querySelector("[data-delete-cancel]");
let pendingExpenseDeleteForm = null;

function submitExpenseDeleteForm(form) {
    if (typeof form.requestSubmit === "function") {
        form.requestSubmit();
        return;
    }

    HTMLFormElement.prototype.submit.call(form);
}

document.addEventListener("click", (event) => {
    if (!(event.target instanceof Element)) {
        return;
    }

    const trigger = event.target.closest("[data-delete-trigger]");
    if (!(trigger instanceof HTMLButtonElement)) {
        return;
    }

    const form = trigger.closest("[data-delete-expense-form]");
    if (!(form instanceof HTMLFormElement)) {
        return;
    }

    if (!expenseDeleteDialog || typeof expenseDeleteDialog.showModal !== "function") {
        if (window.confirm("Are you sure you want to delete this expense?")) {
            submitExpenseDeleteForm(form);
        }
        return;
    }

    pendingExpenseDeleteForm = form;
    expenseDeleteDialog.showModal();
});

expenseDeleteCancelButton?.addEventListener("click", () => {
    pendingExpenseDeleteForm = null;
    expenseDeleteDialog.close();
});

expenseDeleteConfirmButton?.addEventListener("click", () => {
    const form = pendingExpenseDeleteForm;
    pendingExpenseDeleteForm = null;
    expenseDeleteDialog.close();

    if (form instanceof HTMLFormElement) {
        submitExpenseDeleteForm(form);
    }
});

expenseDeleteDialog?.addEventListener("cancel", () => {
    pendingExpenseDeleteForm = null;
});
