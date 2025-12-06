import { Dispatch, SetStateAction, useEffect } from "react";
import { useGlobalNavigationBlocker } from "../providers/BlockNavigationProvider";
import { NavigateOptions } from "next/dist/shared/lib/app-router-context.shared-runtime";

export function useNavigationBlock(
  showDialogSetter: Dispatch<SetStateAction<boolean>>,
): (url: string, options?: NavigateOptions) => void {
  const { blockBack, blockRefresh, unblockBack, unblockRefresh, replace } =
    useGlobalNavigationBlocker();

  useEffect(() => {
    blockRefresh("Refreshing the page will end the call. Are you sure?");
    blockBack(() => {
      showDialogSetter(true);
    });

    return () => {
      unblockBack();
      unblockRefresh();
    };
  }, [blockBack, blockRefresh, unblockBack, unblockRefresh, showDialogSetter]);

  return replace;
}
