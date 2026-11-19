-- OVH Studio: shows OpenVideoHarness's Studio (the console, bin/vh desk) in its window. bin/vh studio --install-icon wrote
-- this applet from tools/desk/launcher/studio.applescript in the clone below; what each click does is bin/vh studio's
-- there, so a git pull changes it with no reinstall. It keeps nothing of its own: the console it started says so in its
-- own info file (owner: icon), and quitting this stops that one only.
--   open it, or click it again: bin/vh studio --icon open (a console in the background if none runs; its one window
--     made, or brought to the front)
--   every minute: bin/vh studio --icon alive (no console any more: this quits too, so the Dock shows what runs)
--   quit it: bin/vh studio --icon quit (the console it started stops, and its window closes; it asks first when an agent
--     in the console is in the middle of a turn). Closing the window alone leaves the console running: an agent may be
--     working, and the next click brings the window back with the conversation where it was

on repoPath()
	return "@@REPO@@"
end repoPath

on vh(args)
	return do shell script "@@ENV@@ cd " & quoted form of repoPath() & " && ./bin/vh studio --icon " & args
end vh

on repoThere()
	try
		do shell script "test -x " & quoted form of (repoPath() & "/bin/vh")
		return true
	on error
		return false
	end try
end repoThere

on openStudio()
	if not repoThere() then
		display dialog "找不到 OpenVideoHarness 了（原来在 " & repoPath() & "）。让 agent 在它现在的位置把 Studio 图标重新装一次（bin/vh studio --install-icon）。" & return & return & "OpenVideoHarness is no longer at " & repoPath() & ". Ask your agent to put the Studio icon back from where it is now (bin/vh studio --install-icon)." buttons {"OK"} default button 1 with title "OVH Studio" with icon caution
		quit
		return
	end if
	try
		vh("open")
	on error msg
		display dialog "Studio 没有打开 / Studio did not open:" & return & return & msg buttons {"OK"} default button 1 with title "OVH Studio" with icon caution
	end try
end openStudio

on run
	openStudio()
end run

on reopen
	openStudio()
end reopen

on idle
	if repoThere() then
		try
			vh("alive")
		on error
			quit
		end try
	end if
	return 60
end idle

on quit
	if repoThere() then
		try
			vh("quit")
		on error msg number n
			if n is 3 then
				set b to button returned of (display dialog msg buttons {"继续开着 Keep it open", "退出 Quit"} default button 1 with title "OVH Studio" with icon caution)
				if b starts with "继续" then return
				try
					vh("quit --force")
				end try
			end if
		end try
	end if
	continue quit
end quit
