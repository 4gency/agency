import {
  AlertDialog,
  AlertDialogBody,
  AlertDialogContent,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogOverlay,
  Button,
} from "@chakra-ui/react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import React from "react"
import { useForm } from "react-hook-form"

import { UsersService } from "../../client"
import useCustomToast from "../../hooks/useCustomToast"

interface DeleteProps {
  title?: string
  message?: string
  isOpen: boolean
  onClose: () => void
  onDelete?: () => Promise<void>
  type?: string
  id?: string
}

const DeleteAlert = ({
  title = "Delete Confirmation",
  message = "Are you sure? You will not be able to undo this action.",
  type,
  id,
  isOpen,
  onClose,
  onDelete,
}: DeleteProps) => {
  const queryClient = useQueryClient()
  const showToast = useCustomToast()
  const cancelRef = React.useRef<HTMLButtonElement | null>(null)
  const {
    handleSubmit,
    formState: { isSubmitting },
  } = useForm()

  const deleteEntity = async (id: string) => {
    if (type === "User") {
      await UsersService.deleteUser({ userId: id })
    } else {
      throw new Error(`Unexpected type: ${type}`)
    }
  }

  const mutation = useMutation({
    mutationFn: id ? () => deleteEntity(id) : undefined,
    onSuccess: () => {
      showToast(
        "Success",
        `The ${type?.toLowerCase()} was deleted successfully.`,
        "success",
      )
      onClose()
    },
    onError: () => {
      showToast(
        "An error occurred.",
        `An error occurred while deleting the ${type?.toLowerCase()}.`,
        "error",
      )
    },
    onSettled: () => {
      if (type === "User") {
        queryClient.invalidateQueries({
          queryKey: ["users"],
        })
      }
    },
  })

  const onSubmit = async () => {
    if (onDelete) {
      try {
        await onDelete()
        onClose()
      } catch (error) {
        console.error("Error in custom delete function:", error)
      }
    } else if (id && type) {
      mutation.mutate()
    }
  }

  return (
    <>
      <AlertDialog
        isOpen={isOpen}
        onClose={onClose}
        leastDestructiveRef={cancelRef}
        size={{ base: "sm", md: "md" }}
        isCentered
      >
        <AlertDialogOverlay>
          <AlertDialogContent as="form" onSubmit={handleSubmit(onSubmit)}>
            <AlertDialogHeader>{title}</AlertDialogHeader>

            <AlertDialogBody>
              {type === "User" && (
                <span>
                  All items associated with this user will also be{" "}
                  <strong>permantly deleted. </strong>
                </span>
              )}
              {message}
            </AlertDialogBody>

            <AlertDialogFooter gap={3}>
              <Button variant="danger" type="submit" isLoading={isSubmitting}>
                Delete
              </Button>
              <Button
                ref={cancelRef}
                onClick={onClose}
                isDisabled={isSubmitting}
              >
                Cancel
              </Button>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialogOverlay>
      </AlertDialog>
    </>
  )
}

export default DeleteAlert
