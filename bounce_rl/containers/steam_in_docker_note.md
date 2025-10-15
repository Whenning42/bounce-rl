Running pressure vessel (specifically using Steam Sniper runtime) inside of docker in a
secure way doesn't appear very tractable.

From this [github thread](https://github.com/containers/bubblewrap/issues/505) and my
own tests, I need to relax seccomp, apparmor, and add CAP_SYS_ADMIN to my docker run
in order for pressure vessel's bwrap version to start successfully (bwrap otherwise
hits Operation not permitted for clone() w/ CLONE_NEWNS to ). Relaxing to this set of
permissions effectively gives root all software in the container which is too risky.

Instead, I'll run pressure vessel outside of the container, with a Bounce launcher
process sitting outside of the Bounce container, allowing for the Bounce app to
launch and kill game instances.